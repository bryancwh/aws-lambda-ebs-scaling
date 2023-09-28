import json
import boto3
import math

def lambda_handler(event, context):
    
    print(event)
    # Add comments
    
    # Get notification metadata
    eventMessage=json.loads(event['Records'][0]['Sns']['Message'])
    volumeid=eventMessage['Trigger']['Metrics'][1]['MetricStat']['Metric']['Dimensions'][0]['value']
    alarmName=eventMessage['AlarmName']
    
    # Modify EBS Volume
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

    iops+=500
    size+=5
    
    # new_size=math.ceil(iops/500)
    
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

    # Modify CW Alarm Threshold
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
    
    threshold+=500
    
    cloudwatchModification = clientCW.put_metric_alarm(
        AlarmName=alarmname,
        AlarmActions=alarmactions,
        EvaluationPeriods=evalperiod,
        ComparisonOperator=comparisonop,
        Metrics=metrics,
        Threshold=threshold
    )
    
    print(cloudwatchModification)  
