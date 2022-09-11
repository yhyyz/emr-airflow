from __future__ import print_function
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import sum

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("""
        Usage: spark-etl.py <s3_input_path> <s3_output_path> 
        """, file=sys.stderr)
        sys.exit(-1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    spark = SparkSession\
        .builder\
        .appName("spark-etl")\
        .getOrCreate()

    sc = spark.sparkContext

    df = spark.read.json(input_path)
    df.write.mode('overwrite').parquet(output_path)

    spark.stop()
