import json
import os
from datetime import timedelta

from airflow import DAG
from airflow.models import Variable
from airflow.operators.dummy import DummyOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.emr_create_job_flow import EmrCreateJobFlowOperator
from airflow.providers.amazon.aws.operators.emr_add_steps import EmrAddStepsOperator
from airflow.providers.amazon.aws.sensors.emr_step import EmrStepSensor
from airflow.utils.dates import days_ago

# ************** AIRFLOW VARIABLES **************
bootstrap_bucket = Variable.get("bootstrap_bucket")
emr_ec2_key_pair = Variable.get("emr_ec2_key_pair")
job_flow_role = Variable.get("job_flow_role")
logs_bucket = Variable.get("logs_bucket")
release_label = Variable.get("release_label")
service_role = Variable.get("service_role")
work_bucket = Variable.get("work_bucket")
# ***********************************************

DAG_ID = os.path.basename(__file__).replace(".py", "")

DEFAULT_ARGS = {
    "owner": "chaopan",
    "depends_on_past": False,
    "email": ["chaopan@amazon.com"],
    "email_on_failure": False,
    "email_on_retry": False,
}


def get_object(key, bucket_name):
    """
    Load S3 object as JSON
    """
    hook = S3Hook()
    content_object = hook.read_key(key=key, bucket_name=bucket_name)
    return json.loads(content_object)


job_flow_config_file = "emr_steps/cluster.json"
emr_job_steps_file = "emr_steps/spark_steps.json"

with DAG(
        dag_id=DAG_ID,
        description="Run multiple Spark jobs with Amazon EMR",
        default_args=DEFAULT_ARGS,
        dagrun_timeout=timedelta(hours=2),
        start_date=days_ago(1),
        schedule_interval=None,
        tags=["airflow emr demo", "spark", "pyspark"],
) as dag:
    begin = DummyOperator(task_id="begin")
    end = DummyOperator(task_id="end")

    cluster_creator = EmrCreateJobFlowOperator(
        task_id="create_job_flow",
        job_flow_overrides=get_object(
            job_flow_config_file, work_bucket
        ),
    )

    # 无需等待集群启动完毕载添加step,只要返回了job_flow id就可以添加steps，step会pending等待集群启动后执行
    step_adder = EmrAddStepsOperator(
        task_id="add_steps",
        job_flow_id="{{ task_instance.xcom_pull(task_ids='create_job_flow', key='return_value') }}",
        aws_conn_id="aws_default",
        steps=get_object(emr_job_steps_file, work_bucket),
    )

    # 在job flow中设置了KeepJobFlowAliveWhenNoSteps为false，因此只要step job运行结束无论成功失败，集群都会自动停止
    step_checker = EmrStepSensor(

        task_id="watch_step",
        job_flow_id="{{ task_instance.xcom_pull('create_job_flow', key='return_value') }}",
        step_id="{{ task_instance.xcom_pull(task_ids='add_steps', key='return_value')[0] }}",
        aws_conn_id="aws_default",
    )

    begin >> cluster_creator >> step_adder >> step_checker >> end
