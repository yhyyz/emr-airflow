#### local install
```shell
# python版本3.7.9, mwaa airflow 版本未2.2.2，apache-airflow-providers-amazon对应版本未2.4.0
# pip install apache-airflow==2.2.2
# pip install apache-airflow-providers-amazon==2.4.0
pip install -r requirements.txt
```

#### sync file to s3
```shell
# emr steps 目录下为job_flow(cluster)配置,spark作业配置,emr启动的bootstrap脚本(按需使用)
aws s3 sync emr_steps/ s3://app-util/emr_steps/ 

# spark elt的一个简单做作业，读取一个S3的json文件，转换为parquet
aws s3 cp  ./scripts/spark-etl.py s3://app-util/scripts/ 

# dag：创建EMR，运行作业，监控状态，关闭集群 
aws s3 cp  dags/emr_step_job.py s3://analytics-airflow-01/dags/   

# 需要注意的是如果定义的steps中有json后缀的文件作为参数，同时使用了airflow变量，需要json后加空格，不要识别为jinja模板
```

#### airflow variables
```shell
# 将variables/common_dag_var.json导入到airflow variables
"bootstrap_bucket": "s3://xxxx/emr_steps/emr_bootstrap.sh", #emr bootstrap脚本地址
"emr_ec2_key_pair": "emr-02", # emr key 
"job_flow_role": "EMR_EC2_DefaultRole", # emr启动的ec2需要权限，比如访问S3,Glue等
"logs_bucket": "s3://xxxx/logs/", # emr logs path
"release_label": "emr-6.6.0",
"service_role": "EMR_DefaultRole", # emr 服务本身需要的权限，比如创建EC2的权限等
"work_bucket": "xxxx", # emr step job及dag中的相关文件的bucket，只需要填写bucket名称即可，不需要s3://
"ec2_subnet_id": "subnet-0f79e4471cfa74ced"
```

#### trigger dag
```
mwaa web ui上执行，查看作业即可
```
![emr-step-dag](https://pcmyp.oss-accelerate.aliyuncs.com/markdown/20220912013407.png)
![emr-step-job](https://pcmyp.oss-accelerate.aliyuncs.com/markdown/20220912013222.png)
