#!/usr/bin/env python3
from __future__ import print_function

import sys

from env import env
from run_common import AWSCli
from run_common import print_message
from run_common import print_session

if __name__ == "__main__":
    from run_common import parse_args

    parse_args()

aws_cli = AWSCli()
aws_availability_zone_nat = env['aws']['AWS_AVAILABILITY_ZONE_NAT']
aws_availability_zone_1 = env['aws']['AWS_AVAILABILITY_ZONE_1']
aws_availability_zone_2 = env['aws']['AWS_AVAILABILITY_ZONE_2']

cidr_vpc = aws_cli.cidr_vpc
cidr_subnet = aws_cli.cidr_subnet

################################################################################
#
# start
#
################################################################################
print_message('get vpc id')

vpc_id = aws_cli.get_vpc_id()
if vpc_id:
    print_message('VPC already exists')
    print('ID: %s \n' % vpc_id)
    print_session('finish python code')
    sys.exit(0)

################################################################################
#
# IAM
#
################################################################################
print_session('create iam role/policy')

################################################################################
print_message('create role')

cmd = ['iam', 'create-role']
cmd += ['--role-name', 'aws-lambda-default-role']
cmd += ['--assume-role-policy-document', 'file://aws_iam/aws-lambda-default-role.json']
aws_cli.run(cmd)

################################################################################
print_message('put role policy')

cmd = ['iam', 'put-role-policy']
cmd += ['--role-name', 'aws-lambda-default-role']
cmd += ['--policy-name', 'aws-lambda-default-policy']
cmd += ['--policy-document', 'file://aws_iam/aws-lambda-default-policy.json']
aws_cli.run(cmd)

################################################################################
#
# VPC
#
################################################################################
print_session('create vpc')

################################################################################
print_message('create vpc')

cmd = ['ec2', 'create-vpc']
cmd += ['--cidr-block', cidr_vpc]
result = aws_cli.run(cmd)
vpc_id = result['Vpc']['VpcId']
aws_cli.set_name_tag(vpc_id, 'av_gateway')

################################################################################
print_message('create subnet')

subnet_id = dict()

cmd = ['ec2', 'create-subnet']
cmd += ['--vpc-id', vpc_id]
cmd += ['--cidr-block', cidr_subnet['public_nat']]
cmd += ['--availability-zone', aws_availability_zone_nat]
result = aws_cli.run(cmd)
subnet_id['public_nat'] = result['Subnet']['SubnetId']
aws_cli.set_name_tag(subnet_id['public_nat'], 'public_nat')

cmd = ['ec2', 'create-subnet']
cmd += ['--vpc-id', vpc_id]
cmd += ['--cidr-block', cidr_subnet['private_1']]
cmd += ['--availability-zone', aws_availability_zone_1]
result = aws_cli.run(cmd)
subnet_id['private_1'] = result['Subnet']['SubnetId']
aws_cli.set_name_tag(subnet_id['private_1'], 'private_1')

cmd = ['ec2', 'create-subnet']
cmd += ['--vpc-id', vpc_id]
cmd += ['--cidr-block', cidr_subnet['private_2']]
cmd += ['--availability-zone', aws_availability_zone_2]
result = aws_cli.run(cmd)
subnet_id['private_2'] = result['Subnet']['SubnetId']
aws_cli.set_name_tag(subnet_id['private_2'], 'private_2')

################################################################################
print_message('create internet gateway')

cmd = ['ec2', 'create-internet-gateway']
result = aws_cli.run(cmd)
internet_gateway_id = result['InternetGateway']['InternetGatewayId']
aws_cli.set_name_tag(internet_gateway_id, 'av_gateway')

################################################################################
print_message('attach internet gateway')

cmd = ['ec2', 'attach-internet-gateway']
cmd += ['--internet-gateway-id', internet_gateway_id]
cmd += ['--vpc-id', vpc_id]
aws_cli.run(cmd)

################################################################################
print_message('create eip')

cmd = ['ec2', 'allocate-address']
cmd += ['--domain', 'vpc']
result = aws_cli.run(cmd)
eip_id = result['AllocationId']

################################################################################
print_message('create nat gateway')

cmd = ['ec2', 'create-nat-gateway']
cmd += ['--subnet-id', subnet_id['public_nat']]
cmd += ['--allocation-id', eip_id]
result = aws_cli.run(cmd)
nat_gateway_id = result['NatGateway']['NatGatewayId']

################################################################################
print_message('create route table')

route_table_id = dict()

cmd = ['ec2', 'create-route-table']
cmd += ['--vpc-id', vpc_id]
result = aws_cli.run(cmd)
route_table_id['public_nat'] = result['RouteTable']['RouteTableId']
aws_cli.set_name_tag(route_table_id['public_nat'], 'public_nat')

cmd = ['ec2', 'create-route-table']
cmd += ['--vpc-id', vpc_id]
result = aws_cli.run(cmd)
route_table_id['private'] = result['RouteTable']['RouteTableId']
aws_cli.set_name_tag(route_table_id['private'], 'private')

################################################################################
print_message('associate route table')

cmd = ['ec2', 'associate-route-table']
cmd += ['--subnet-id', subnet_id['public_nat']]
cmd += ['--route-table-id', route_table_id['public_nat']]
aws_cli.run(cmd)

cmd = ['ec2', 'associate-route-table']
cmd += ['--subnet-id', subnet_id['private_1']]
cmd += ['--route-table-id', route_table_id['private']]
aws_cli.run(cmd)

cmd = ['ec2', 'associate-route-table']
cmd += ['--subnet-id', subnet_id['private_2']]
cmd += ['--route-table-id', route_table_id['private']]
aws_cli.run(cmd)

################################################################################
print_message('create route')

cmd = ['ec2', 'create-route']
cmd += ['--route-table-id', route_table_id['public_nat']]
cmd += ['--destination-cidr-block', '0.0.0.0/0']
cmd += ['--gateway-id', internet_gateway_id]
aws_cli.run(cmd)

cmd = ['ec2', 'create-route']
cmd += ['--route-table-id', route_table_id['private']]
cmd += ['--destination-cidr-block', '0.0.0.0/0']
cmd += ['--nat-gateway-id', nat_gateway_id]
aws_cli.run(cmd)

################################################################################
print_message('create security group')

security_group_id = dict()

cmd = ['ec2', 'create-security-group']
cmd += ['--group-name', 'public_nat']
cmd += ['--description', 'public_nat']
cmd += ['--vpc-id', vpc_id]
result = aws_cli.run(cmd)
security_group_id['public_nat'] = result['GroupId']

cmd = ['ec2', 'create-security-group']
cmd += ['--group-name', 'private']
cmd += ['--description', 'private']
cmd += ['--vpc-id', vpc_id]
result = aws_cli.run(cmd)
security_group_id['private'] = result['GroupId']

################################################################################
print_message('authorize security group ingress')

cmd = ['ec2', 'authorize-security-group-ingress']
cmd += ['--group-id', security_group_id['public_nat']]
cmd += ['--protocol', 'all']
cmd += ['--cidr', '0.0.0.0/0']
aws_cli.run(cmd)

cmd = ['ec2', 'authorize-security-group-ingress']
cmd += ['--group-id', security_group_id['private']]
cmd += ['--protocol', 'all']
cmd += ['--cidr', '0.0.0.0/0']
aws_cli.run(cmd)
