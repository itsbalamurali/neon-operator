import base64
from typing import Optional

import jwt
import kopf
import kubernetes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from kubernetes.client import ApiException


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


def generate_jwt(private_key: Ed25519PrivateKey, claims: Optional[dict] = None) -> str:
    """
    Generate a JWT token using the provided claims and private key
    :param claims: A dictionary of claims to include in the JWT
    :param private_key: The private key to sign the JWT with
    :return:
    """
    jwt_token = jwt.encode(claims, key=private_key.encode(), algorithm="ED25519")
    return jwt_token


def neon_secret(
        namespace: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
) -> kubernetes.client.V1Secret:
    """
    Create a secret for Neon storage credentials
    :param namespace: The namespace to create the secret in
    :param aws_access_key_id: The AWS access key ID
    :param aws_secret_access_key: The AWS secret access key
    :return: A kubernetes secret object
    """

    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

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
            "AUTH_PRIVATE_KEY": base64.b64encode(private_key_pem).decode("utf-8"),
            "AUTH_PUBLIC_KEY": base64.b64encode(public_key_pem).decode("utf-8"),
        },
    )
    return secret
