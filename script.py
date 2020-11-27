#Imports
import boto3
from decouple import config
import os
from botocore.exceptions import ClientError


#Definindo as variáveis
REGION_OH = "us-east-2"
REGION_NV = "us-west-2"


#Criando sessões
session_oh = boto3.session.Session(region_name=REGION_OH)

session_nv = boto3.session.Session(region_name=REGION_NV)


#Criando clientes
ec2_oh = boto3.resource("ec2", region_name=REGION_OH)
ec2_nv = boto3.resource("ec2", region_name=REGION_NV)
client_oh = boto3.client("ec2", region_name=REGION_OH)
client_nv = boto3.client("ec2", region_name=REGION_NV)


#Criando chave
key_name_oh = "mikomoares_oh1"
key_name_nv = "mikomoares_nv1"

try:
    print("Criando chave")
    key_file_name = "/home/mikomoares/{}.pem".format(key_name_oh)
    key_response = client_oh.create_key_pair(KeyName=key_name_oh)
    with open(key_file_name, "w") as f: f.write(key_response['KeyMaterial'])
    os.system("chmod 400 {}".format(key_file_name))
    print("chave criada com sucesso")
except:
    print("chave já existente")

try:
    print("Criando chave")
    key_file_name = "/home/mikomoares/{}.pem".format(key_name_nv)
    key_response = client_nv.create_key_pair(KeyName=key_name_nv)
    with open(key_file_name, "w") as f: f.write(key_response['KeyMaterial'])
    os.system("chmod 400 {}".format(key_file_name))
    print("chave criada com sucesso")
except:
    print("chave já existente")


#Criando security group
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
    print('Security Group criado com sucesso %s vpc %s.' % (security_group_id_oh, vpc_id))

    data = client_oh.authorize_security_group_ingress(
        GroupId=security_group_id_oh,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 80,
             'ToPort': 80,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol':'tcp',
             'FromPort': 5432,
             'ToPort': 5432,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ])
    print("Security group {} criado com sucesso".format(security_group_name_oh))
except ClientError as e:
    print(e)



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
    print('Security Group criado com sucesso %s vpc %s.' % (security_group_id_nv, vpc_id))

    data = client_nv.authorize_security_group_ingress(
        GroupId=security_group_id_nv,
        IpPermissions=[
            {'IpProtocol': 'tcp',
             'FromPort': 80,
             'ToPort': 80,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol':'tcp',
             'FromPort': 5432,
             'ToPort': 5432,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ])
    print("Security group {} criado com sucesso".format(security_group_name_nv))
except ClientError as e:
    print(e)


#Criando scripts
user_data_oh = '''#!/bin/bash
     sudo apt update
     sudo apt install postgresql postgresql-contrib -y
     sudo -u postgres sh -c "psql -c \\"CREATE USER cloud WITH PASSWORD 'cloud';\\" && createdb -O cloud tasks"
     sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" /etc/postgresql/10/main/postgresql.conf
     sudo sed -i "a\host all all 0.0.0.0/0 md5" /etc/postgresql/10/main/pg_hba.conf
     sudo systemctl restart postgresql
     '''

#Criando instancias
ec2_oh.create_instances(
    ImageId="ami-0dd9f0e7df0f0a138",
    SecurityGroupIds=[security_group_name_oh],
    KeyName=key_name_oh,
    MinCount=1,
    MaxCount=1,
    UserData = user_data_oh,
    InstanceType="t2.micro",
    TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'nome', 'Value': 'Postgress',},],},]
)

print("Instancia Ohio criada com sucesso")


ec2_nv.create_instances(
    ImageId="ami-0ac73f33a1888c64a",
    SecurityGroupIds=[security_group_name_nv],
    KeyName=key_name_nv,
    MinCount=1,
    MaxCount=1,
    InstanceType="t2.micro",
    TagSpecifications=[{'ResourceType': 'instance', 'Tags': [{'Key': 'Name', 'Value': 'NV',},],},]
)

print("Instancia North Virginia criada com sucesso")
