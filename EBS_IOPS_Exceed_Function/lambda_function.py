import json
import boto3
import math

def lambda_handler(event, context):
    
    # Get volumeId and alarmName from event metadata
    eventMessage=json.loads(event['Records'][0]['Sns']['Message'])
    volumeid=eventMessage['Trigger']['Metrics'][1]['MetricStat']['Metric']['Dimensions'][0]['value']
    alarmName=eventMessage['AlarmName'] 


    # Modify the EBS volume

    # Get volume metadata from ec2 client 
    client = boto3.client('ec2')
    
    metadata = client.describe_volumes(
        VolumeIds=[
            volumeid,
        ],
    )
    
    size=metadata['Volumes'][0]['Size']
    volumetype=metadata['Volumes'][0]['VolumeType' ]
    iops=metadata['Volumes'][0]['Iops']
    throughput=metadata['Volumes'][0]['Throughput']
    multiattachenabled=metadata['Volumes'][0]['MultiAttachEnabled']

    # Define increment of IOPS & Size
    iops+=500
    
    # IOPS to Size ratio must not exceed 500
    print("Checking IOPS to Size ratio...")
    if iops/size >= 500:
        
        print("IOPS to Size ratio exceeded, increasing Volume Size...")
        size = math.ceil(iops/500) + 5 
        
    else:
        print("IOPS to Size ratio check good, within 500")
    
    # EBS volume modification
    response = client.modify_volume(
        DryRun=False,
        VolumeId=volumeid,
        Size=size,
        VolumeType=volumetype,
        Iops=iops,
        Throughput=throughput,
        MultiAttachEnabled=multiattachenabled
    )
    
    print(response)
    
    print("Successfully increased Volume Iops to: " + str(iops))


    # Modify the CloudWatch Alarm threshold

    # Get alarm metadata from CloudWatch client
    clientCW = boto3.client('cloudwatch')

    alarmMetadata = clientCW.describe_alarms(
        AlarmNames=[
            alarmName,
        ]
    )

    alarmname=alarmMetadata['MetricAlarms'][0]['AlarmName']
    alarmactions=alarmMetadata['MetricAlarms'][0]['AlarmActions']
    evalperiod=alarmMetadata['MetricAlarms'][0]['EvaluationPeriods']
    comparisonop=alarmMetadata['MetricAlarms'][0]['ComparisonOperator']
    metrics=alarmMetadata['MetricAlarms'][0]['Metrics']
    threshold= alarmMetadata['MetricAlarms'][0]['Threshold']
    
    # Set threshold to 70% of set level of IOPS 
    threshold = 0.7*iops 
    
    # CW alarm threshold modification 
    cloudwatchModification = clientCW.put_metric_alarm(
        AlarmName=alarmname,
        AlarmActions=alarmactions,
        EvaluationPeriods=evalperiod,
        ComparisonOperator=comparisonop,
        Metrics=metrics,
        Threshold=threshold
    )
    
    print(cloudwatchModification)  

    print("Successfully increased CloudWatch Alarm threshold to: " + str(threshold))