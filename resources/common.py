import base64

import kopf
import kubernetes
from kubernetes.client import ApiException
import nacl.signing
import jwt

def deploy_secret(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
):
    secret = neon_secret(namespace, aws_access_key_id, aws_secret_access_key)
    kopf.adopt(secret)
    api_instance = kubernetes.client.CoreV1Api(kube_client)
    try:
        api_instance.create_namespaced_secret(namespace=namespace, body=secret)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def update_secret(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
):
    secret = neon_secret(namespace, aws_access_key_id, aws_secret_access_key)
    api_instance = kubernetes.client.CoreV1Api(kube_client)
    try:
        api_instance.patch_namespaced_secret(namespace=namespace, name="neon-storage-credentials", body=secret)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def delete_secret(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
):
    api_instance = kubernetes.client.CoreV1Api(kube_client)
    try:
        api_instance.delete_namespaced_secret(namespace=namespace, name="neon-storage-credentials")
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)

# Generate ed25519 keypair using pynacl
def generate_keypair()-> (nacl.signing.SigningKey, nacl.signing.VerifyKey):
    private_key = nacl.signing.SigningKey.generate()
    public_key = private_key.verify_key
    return private_key, public_key

def generate_jwt(claims: dict, private_key: nacl.signing.SigningKey) -> str:
    """
    Generate a JWT token using the provided claims and private key
    :param claims:
    :param private_key:
    :return:
    """
    jwt_token = jwt.encode({"some": "payload"}, "secret", algorithm="HS512")
    return jwt_token

def neon_secret(
        namespace: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
) -> kubernetes.client.V1Secret:
    """
    Create a secret for Neon storage credentials
    :param aws_access_key_id:
    :param aws_secret_access_key:
    :return:
    """

    (private_key, public_key) = generate_keypair()

    secret = kubernetes.client.V1Secret(
        api_version="v1",
        kind="Secret",
        metadata=kubernetes.client.V1ObjectMeta(
            name="neon-storage-credentials",
            namespace=namespace,
        ),
        data={
            "AWS_ACCESS_KEY_ID": base64.b64encode(aws_access_key_id.encode("utf-8")).decode("utf-8"),
            "AWS_SECRET_ACCESS_KEY": base64.b64encode(aws_secret_access_key.encode("utf-8")).decode("utf-8"),
            "AUTH_PRIVATE_KEY": base64.b64encode(private_key.encode()).decode("utf-8"),
            "AUTH_PUBLIC_KEY": base64.b64encode(public_key.encode()).decode("utf-8"),
        },
    )
    return secret
