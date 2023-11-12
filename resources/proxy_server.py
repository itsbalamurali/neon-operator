import kopf
import kubernetes
from kubernetes.client import ApiException


def deploy_proxy_server(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        image: str = "neondatabase/neon",
        replicas: int = 1,
):
    deployment = proxy_server_deployment(namespace, image, replicas)
    service = proxy_server_service(namespace)
    kopf.adopt(deployment)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.create_namespaced_deployment(namespace=namespace, body=deployment)
        core_client.create_namespaced_service(namespace=namespace, body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def update_proxy_server(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
        image: str = "neondatabase/neon",
        replicas: int = 1,
):
    deployment = proxy_server_deployment(namespace, image, replicas)
    service = proxy_server_service(namespace)
    kopf.adopt(deployment)
    kopf.adopt(service)

    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.patch_namespaced_deployment(namespace=namespace, name="proxy-server", body=deployment)
        core_client.patch_namespaced_service(namespace=namespace, name="proxy-server", body=service)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def delete_proxy_server(
        kube_client: kubernetes.client.ApiClient,
        namespace: str,
):
    apps_client = kubernetes.client.AppsV1Api(kube_client)
    core_client = kubernetes.client.CoreV1Api(kube_client)
    try:
        apps_client.delete_namespaced_deployment(namespace=namespace, name="proxy-server")
        core_client.delete_namespaced_service(namespace=namespace, name="proxy-server")
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def proxy_server_deployment(
        namespace: str,
        image: str,
        replicas: int,
) -> kubernetes.client.V1Deployment:
    template = kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(
            labels={"app": "proxy-server"},
        ),
        spec=kubernetes.client.V1PodSpec(
            containers=[
                kubernetes.client.V1Container(
                    name="proxy-server",
                    image=image,
                    command=["proxy_server", "--listen-addr="],
                    ports=[
                        kubernetes.client.V1ContainerPort(
                            container_port=8080,
                            name="http",
                        ),
                    ],
                ),
            ],
        ),
    )

    spec = kubernetes.client.V1DeploymentSpec(
        replicas=replicas,
        selector=kubernetes.client.V1LabelSelector(
            match_labels={"app": "proxy-server"},
        ),
        template=template,
    )

    deployment = kubernetes.client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=kubernetes.client.V1ObjectMeta(
            name="proxy-server",
            namespace=namespace,
        ),
        spec=spec,
    )

    return deployment


def proxy_server_service(
        namespace: str,
) -> kubernetes.client.V1Service:
    spec = kubernetes.client.V1ServiceSpec(
        selector={"app": "proxy-server"},
        ports=[
            kubernetes.client.V1ServicePort(port=8080, name="http", target_port=8080),
        ],
    )

    service = kubernetes.client.V1Service(
        api_version="v1",
        kind="Service",
        metadata=kubernetes.client.V1ObjectMeta(
            name="proxy-server",
            namespace=namespace,
        ),
        spec=spec,
    )

    return service