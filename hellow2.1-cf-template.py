"""Generating CloudFormation template."""

from troposphere import (
        Base64,
        ec2,
        GetAtt,
        Join,
        Output,
        Parameter,
        Ref,
        Template,
)

from troposphere.ec2 import (
    EIP,
    VPC,
    Instance,
    InternetGateway,
    NetworkAcl,
    NetworkAclEntry,
    NetworkInterfaceProperty,
    PortRange,
    Route,
    RouteTable,
    SecurityGroup,
    SecurityGroupRule,
    Subnet,
    SubnetNetworkAclAssociation,
    SubnetRouteTableAssociation,
    VPCGatewayAttachment,
)

ApplicationPort = "3000"
t = Template()

t.set_description("Effective DevOps in AWS: HelloWorld web application")

#Create VPC
t.add_resource(
    VPC("VPC", CidrBlock="192.0.0.0/16")
)

subnet = t.add_resource(ec2.Subnet(
        "Subnet",
        AvailabilityZone="ap-northeast-2c",
        CidrBlock="192.0.0.0/24",
        MapPublicIpOnLaunch=True,
        VpcId=Ref("VPC"),
))

internetGateway = t.add_resource(
    InternetGateway("InternetGateway")
)

gatewayAttachment = t.add_resource(
    VPCGatewayAttachment(
        "AttachGateway", VpcId=Ref("VPC"), InternetGatewayId=Ref(internetGateway)
    )
)

routeTable = t.add_resource(
    RouteTable("RouteTable", VpcId=Ref("VPC"))
)

route = t.add_resource(
    Route(
        "Route",
        DependsOn="AttachGateway",
        GatewayId=Ref("InternetGateway"),
        DestinationCidrBlock="0.0.0.0/0",
        RouteTableId=Ref(routeTable),
    )
)

subnetRouteTableAssociation = t.add_resource(
    SubnetRouteTableAssociation(
        "SubnetRouteTableAssociation",
        SubnetId=Ref(subnet),
        RouteTableId=Ref(routeTable),
    )
)

t.add_parameter(Parameter(
    "KeyPair",
    Description="Name of an existing EC2 KeyPair to SSH",
    Type="AWS::EC2::KeyPair::KeyName",
    ConstraintDescription="must be the name of an existing EC2 KeyPair.",
))

ec2sg = t.add_resource(ec2.SecurityGroup(
    "DevOpsSG",
    GroupDescription="Allow SSH and TCP/{} access".format(ApplicationPort),
    SecurityGroupIngress=[
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort="22",
            ToPort="22",
            CidrIp="0.0.0.0/0",
        ),
        ec2.SecurityGroupRule(
            IpProtocol="tcp",
            FromPort=ApplicationPort,
            ToPort=ApplicationPort,
            CidrIp="0.0.0.0/0",
        ),
    ],
    VpcId=Ref("VPC"),
))


ud = Base64(Join('\n', [
    "#!/bin/bash",
    "sudo curl --silent --location https://rpm.nodesource.com/setup_14.x | bash -",
    "sudo yum -y install nodejs"
    "wget http://bit.ly/2vESNuc -O /home/ec2-user/helloworld.js",
    "wget http://bit.ly/2vVvT18 -O /etc/init/helloworld.conf",
    "start helloworld"
]))

t.add_resource(ec2.Instance(
    "instance",
    ImageId="ami-07464b2b9929898f8",
    InstanceType="t2.micro",
    SecurityGroupIds=[Ref(ec2sg)],
    KeyName=Ref("KeyPair"),
    UserData=ud,
    SubnetId=Ref(subnet),
))

t.add_output(Output(
    "InstancePublicIp",
    Description="Public IP of our instance.",
    Value=GetAtt("instance", "PublicIp"),
))

t.add_output(Output(
    "WebUrl",
    Description="Application endpoint",
    Value=Join("", [
        "http://", GetAtt("instance", "PublicDnsName"),
        ":", ApplicationPort
    ]),
))

print(t.to_json())
