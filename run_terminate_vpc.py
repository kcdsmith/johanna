#!/usr/bin/env python3
from __future__ import print_function

from run_common import AWSCli
from run_common import print_message
from run_common import print_session

if __name__ == "__main__":
    from run_common import parse_args

    parse_args()

aws_cli = AWSCli()

cidr_vpc = aws_cli.cidr_vpc

################################################################################
#
# start
#
################################################################################
print_session('terminate vpc')

################################################################################
print_message('get vpc id')

vpc_id = aws_cli.get_vpc_id()

################################################################################
print_message('delete security group')

cmd = ['ec2', 'describe-security-groups']
result = aws_cli.run(cmd, ignore_error=True)
for r in result['SecurityGroups']:
    if r['VpcId'] != vpc_id:
        continue
    if r['GroupName'] == 'default':
        continue
    print('delete security group (id: %s)' % r['GroupId'])
    cmd = ['ec2', 'delete-security-group']
    cmd += ['--group-id', r['GroupId']]
    aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('delete route')

cmd = ['ec2', 'describe-route-tables']
result = aws_cli.run(cmd, ignore_error=True)
for r in result['RouteTables']:
    if r['VpcId'] != vpc_id:
        continue
    for route in r['Routes']:
        if route['DestinationCidrBlock'] == '0.0.0.0/0':
            print('delete route (route table id: %s)' % r['RouteTableId'])
            cmd = ['ec2', 'delete-route']
            cmd += ['--route-table-id', r['RouteTableId']]
            cmd += ['--destination-cidr-block', '0.0.0.0/0']
            aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('disassociate route table')

cmd = ['ec2', 'describe-route-tables']
result = aws_cli.run(cmd, ignore_error=True)
for r in result['RouteTables']:
    if r['VpcId'] != vpc_id:
        continue
    for association in r['Associations']:
        if association['Main']:
            continue
        print('disassociate route table (route table id: %s, route table association id: %s)' %
              (r['RouteTableId'], association['RouteTableAssociationId']))
        cmd = ['ec2', 'disassociate-route-table']
        cmd += ['--association-id', association['RouteTableAssociationId']]
        aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('delete route table')

cmd = ['ec2', 'describe-route-tables']
result = aws_cli.run(cmd, ignore_error=True)
for r in result['RouteTables']:
    if r['VpcId'] != vpc_id:
        continue
    if len(r['Associations']) != 0:
        continue
    print('delete route table (route table id: %s)' % r['RouteTableId'])
    cmd = ['ec2', 'delete-route-table']
    cmd += ['--route-table-id', r['RouteTableId']]
    aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('delete nat gateway')

cmd = ['ec2', 'describe-nat-gateways']
result = aws_cli.run(cmd, ignore_error=True)
for r in result['NatGateways']:
    if r['VpcId'] != vpc_id:
        continue
    print('delete nat gateway (nat gateway id: %s)' % r['NatGatewayId'])
    cmd = ['ec2', 'delete-nat-gateway']
    cmd += ['--nat-gateway-id', r['NatGatewayId']]
    aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('wait delete nat gateway')

aws_cli.wait_delete_nat_gateway()

################################################################################
print_message('release eip')

cmd = ['ec2', 'describe-addresses']
result = aws_cli.run(cmd, ignore_error=True)
for r in result['Addresses']:
    print('release address (address id: %s)' % r['AllocationId'])
    cmd = ['ec2', 'release-address']
    cmd += ['--allocation-id', r['AllocationId']]
    aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('detach internet gateway')

cmd = ['ec2', 'describe-internet-gateways']
result = aws_cli.run(cmd, ignore_error=True)
for r in result['InternetGateways']:
    if len(r['Attachments']) != 1:
        continue
    if r['Attachments'][0]['VpcId'] != vpc_id:
        continue
    print('detach internet gateway (internet gateway id: %s)' % r['InternetGatewayId'])
    cmd = ['ec2', 'detach-internet-gateway']
    cmd += ['--internet-gateway-id', r['InternetGatewayId']]
    cmd += ['--vpc-id', r['Attachments'][0]['VpcId']]
    aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('delete internet gateway')

cmd = ['ec2', 'describe-internet-gateways']
result = aws_cli.run(cmd, ignore_error=True)
for r in result['InternetGateways']:
    if len(r['Attachments']) != 0:
        continue
    print('delete internet gateway (internet gateway id: %s)' % r['InternetGatewayId'])
    cmd = ['ec2', 'delete-internet-gateway']
    cmd += ['--internet-gateway-id', r['InternetGatewayId']]
    aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('delete subnet')

cmd = ['ec2', 'describe-subnets']
result = aws_cli.run(cmd, ignore_error=True)
for r in result['Subnets']:
    if r['VpcId'] != vpc_id:
        continue
    print('delete subnet (subnet id: %s)' % r['SubnetId'])
    cmd = ['ec2', 'delete-subnet']
    cmd += ['--subnet-id', r['SubnetId']]
    aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('delete vpc')

if vpc_id:
    print('delete vpc (vpc id: %s)' % vpc_id)
    cmd = ['ec2', 'delete-vpc']
    cmd += ['--vpc-id', vpc_id]
    aws_cli.run(cmd, ignore_error=True)

################################################################################
#
# IAM
#
################################################################################
print_session('terminate iam role/policy')

################################################################################
print_message('delete role policy')

cmd = ['iam', 'delete-role-policy']
cmd += ['--role-name', 'aws-lambda-default-role']
cmd += ['--policy-name', 'aws-lambda-default-policy']
aws_cli.run(cmd, ignore_error=True)

################################################################################
print_message('delete role')

cmd = ['iam', 'delete-role']
cmd += ['--role-name', 'aws-lambda-default-role']
aws_cli.run(cmd, ignore_error=True)
