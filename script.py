#Imports
import boto3
from decouple import config
import os
from botocore.exceptions import ClientError
import time


#Definindo as variáveis
REGION_OH = "us-east-2"
REGION_NV = "us-west-2"


#Criando sessões
session_oh = boto3.session.Session(region_name=REGION_OH)

session_nv = boto3.session.Session(region_name=REGION_NV)


#Criando clientes
print("conectando......")
ec2_oh = boto3.resource("ec2", region_name=REGION_OH)
ec2_nv = boto3.resource("ec2", region_name=REGION_NV)
client_oh = boto3.client("ec2", region_name=REGION_OH)
client_nv = boto3.client("ec2", region_name=REGION_NV)
client_lb = boto3.client('elb', region_name=REGION_NV)
client_as = boto3.client('autoscaling', region_name=REGION_NV)
client = boto3.client('autoscaling', region_name=REGION_NV)



#Criando chave
key_name_oh = "mikomoares_oh1"
key_name_nv = "mikomoares_nv1"

try:
    print("Criando chave......")
    key_file_name = "/home/mikomoares/{}.pem".format(key_name_oh)
    key_response = client_oh.create_key_pair(KeyName=key_name_oh)
    with open(key_file_name, "w") as f: f.write(key_response['KeyMaterial'])
    os.system("chmod 400 {}".format(key_file_name))
    print("chave criada com sucesso (;")
except:
    print("chave já existente /:")

try:
    print("Criando chave......")
    key_file_name = "/home/mikomoares/{}.pem".format(key_name_nv)
    key_response = client_nv.create_key_pair(KeyName=key_name_nv)
    with open(key_file_name, "w") as f: f.write(key_response['KeyMaterial'])
    os.system("chmod 400 {}".format(key_file_name))
    print("chave criada com sucesso (;")
except:
    print("chave já existente /:")


#Criando security group
print("criando security group......")
security_group_name_oh = "security1"
security_response = client_oh.describe_security_groups()
for i in security_response['SecurityGroups']:
    if i['GroupName'] == security_group_name_oh:
        client_oh.delete_security_group(GroupName=security_group_name_oh)

response = client_oh.describe_vpcs()
vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

try:
    response = client_oh.create_security_group(GroupName=security_group_name_oh,
                                         Description='DESCRIPTION',
                                         VpcId=vpc_id)
    security_group_id_oh = response['GroupId']

    data = client_oh.authorize_security_group_ingress(
        GroupId=security_group_id_oh,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol':'tcp',
             'FromPort': 5432,
             'ToPort': 5432,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ])
    print("Security group {} criado com sucesso (;".format(security_group_name_oh))
except ClientError as e:
    print(e)


print("criando security group......")
security_group_name_nv = "security2"
security_response = client_nv.describe_security_groups()
for i in security_response['SecurityGroups']:
    if i['GroupName'] == security_group_name_nv:
        client_nv.delete_security_group(GroupName=security_group_name_nv)

response = client_nv.describe_vpcs()
vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

try:
    response = client_nv.create_security_group(GroupName=security_group_name_nv,
                                         Description='DESCRIPTION',
                                         VpcId=vpc_id)
    security_group_id_nv = response['GroupId']

    data = client_nv.authorize_security_group_ingress(
        GroupId=security_group_id_nv,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 8080,
             'ToPort': 8080,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        ])
    print("Security group {} criado com sucesso (;".format(security_group_name_nv))
except ClientError as e:
    print(e)


#Criando scripts e instancia ohio
print("criando instancia postgress(oh)......")
user_data_oh = '''#!/bin/bash
     sudo apt update
     sudo apt install postgresql postgresql-contrib -y
     sudo -u postgres sh -c "psql -c \\"CREATE USER cloud WITH PASSWORD 'cloud';\\" && createdb -O cloud tasks"
     sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/10/main/postgresql.conf
     sudo sed -i "a\host all all 0.0.0.0/0 md5" /etc/postgresql/10/main/pg_hba.conf
     sudo systemctl restart postgresql
     '''
waiter = client_oh.get_waiter('instance_status_ok')
instance_oh = ec2_oh.create_instances(
    ImageId="ami-0dd9f0e7df0f0a138",
    SecurityGroupIds=[security_group_id_oh],
    KeyName=key_name_oh,
    MinCount=1,
    MaxCount=1,
    UserData = user_data_oh,
    InstanceType="t2.micro",
    TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Postgres'}]}]
)
waiter.wait(InstanceIds=[instance_oh[0].id])

print("Instancia postgress(oh) criada com sucesso (;")


#Criando script e instancia north virginia
print("criando instancia Django(nv)......")
user_data_nv = '''#!/bin/sh
     cd /home/ubuntu
     sudo apt update
     git clone https://github.com/mikomoares/tasks.git 
     sudo sed -i "s/node1/{}/g" /home/ubuntu/tasks/portfolio/settings.py 
     cd tasks
     ./install.sh
     cd ..
     reboot
     '''.format(client_oh.describe_instances(InstanceIds=[instance_oh[0].id])['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['PrivateIpAddresses'][0]['Association']['PublicIp'])

instance_nv = ec2_nv.create_instances(
    ImageId="ami-0ac73f33a1888c64a",
    SecurityGroupIds=[security_group_id_nv],
    KeyName=key_name_nv,
    MinCount=1,
    MaxCount=1,
    UserData = user_data_nv,
    InstanceType="t2.micro",
    TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'Django'}]}]
)
instance_nv[0].wait_until_running()

print("Instancia North Virginia criada com sucesso (;")


#Cria imagem da ORM
print("criando imagem de django.....")
waiter = client_nv.get_waiter('image_available')
image = client_nv.create_image(InstanceId=instance_nv[0].id, NoReboot=True, Name="Django image")
waiter.wait(ImageIds=[image["ImageId"]])
print("imagem de Django criada (;")


#Deletando instancia Django
try:
    print("deletando instancia base de Django......")
    all_instaces = ec2_nv.instances.filter(Filters=[
        {'Name': 'tag:Name', 'Values': ['Django']}
    ])
    instaces_id = []
    for instance in all_instaces:
        instaces_id.append(instance.id)
        waiter = client_nv.get_waiter('instance_terminated')
        all_instaces.terminate()
        waiter.wait(InstanceIds=instaces_id)        
    print ("Instancia deletada (;")
except:
        print("\nERRO:", e)


#Cria LoadBalance
print("criando Load Balancer......")
client_lb.create_load_balancer(
    LoadBalancerName="LoadBalancer",
    Listeners=[
        {
            'Protocol':'HTTP',
            'LoadBalancerPort':8080,
            'InstancePort':8080
        }
    ],
    AvailabilityZones=[
        'us-west-2a',
        'us-west-2b',
        'us-west-2c',
        'us-west-2d',
    ],
    SecurityGroups=[security_group_id_nv],
    Tags=[
        {'Key': 'Name', 'Value': 'LoadBalancer'}
    ]
)
time.sleep(10)
print("Load Balance criado com sucesso (;")



#Cria Launch Configuration
print("criando Launch Configuration......")
client_as.create_launch_configuration(
    LaunchConfigurationName="LaunchConfiguration",
    ImageId=image["ImageId"],
    KeyName=key_name_nv,
    SecurityGroups=[security_group_id_nv],
    InstanceType='t2.micro'
)
print("Launch Configuration criado com sucesso (;")


#Cria Auto Scaling
print("criando Auto Scaling......")
client.create_auto_scaling_group(
    AutoScalingGroupName="AutoScalingGroup",
    LaunchConfigurationName="LaunchConfiguration",
    MinSize=2,
    MaxSize=5,
    DesiredCapacity=2,
    AvailabilityZones=[
        'us-west-2a', 
        'us-west-2b', 
        'us-west-2c',
        'us-west-2d', 
    ],
    LoadBalancerNames=["LoadBalancer"],
)
print("Auto Scaling criado com sucesso (;")