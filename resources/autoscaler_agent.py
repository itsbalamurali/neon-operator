import kopf
import kubernetes
from kubernetes.client import ApiException


def deploy_autoscaler_agent(
        kube_client: kubernetes.client.CoreV1Api,
        namespace: str,
        image: str = "neondatabase/neon:latest",
        replicas: int = 1,
):
    """
    Deploy the autoscaler agent to the cluster
    :param kube_client: The kubernetes client to use
    :param namespace: The namespace to deploy to
    :param image: The image to use for the deployment
    :param replicas: The number of replicas to deploy
    :return:
    """
    deployment = autoscaler_agent_deployment(replicas, image)
    kopf.adopt(deployment)
    apps_client = kubernetes.client.AppsV1Api(kube_client)

    try:
        apps_client.create_namespaced_deployment(namespace=namespace, body=deployment)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def update_autoscaler_agent(
        kube_client: kubernetes.client.CoreV1Api,
        namespace: str,
        image: str = "neondatabase/neon:latest",
        replicas: int = 1,
):
    deployment = autoscaler_agent_deployment(replicas, image)
    kopf.adopt(deployment)
    apps_client = kubernetes.client.AppsV1Api(kube_client)

    try:
        apps_client.patch_namespaced_deployment(namespace=namespace, name="autoscaler-agent", body=deployment)
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def delete_autoscaler_agent(
        kube_client: kubernetes.client.CoreV1Api,
        namespace: str,
):
    apps_client = kubernetes.client.AppsV1Api(kube_client)
    try:
        apps_client.delete_namespaced_deployment(namespace=namespace, name="autoscaler-agent")
    except ApiException as e:
        print("Exception when calling Api: %s\n" % e)


def autoscaler_agent_deployment(
        replicas: int,
        image: str,
) -> kubernetes.client.V1Deployment:
    """
    Generate a deployment for the autoscaler agent
    :param replicas: The number of replicas to deploy
    :param image: The image to use for the deployment
    :return: A kubernetes deployment object
    """

    deployment = kubernetes.client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=kubernetes.client.V1ObjectMeta(
            name="autoscaler-agent",
            labels={"app": "autoscaler-agent"},
        ),
        spec=kubernetes.client.V1DeploymentSpec(
        replicas=1,
        selector=kubernetes.client.V1LabelSelector(
            match_labels={"app": "autoscaler-agent"},
        ),
        template=kubernetes.client.V1PodTemplateSpec(
        metadata=kubernetes.client.V1ObjectMeta(
            labels={"app": "autoscaler-agent"},
        ),
        spec=kubernetes.client.V1PodSpec(
            containers=[
                kubernetes.client.V1Container(
                    name="autoscaler-agent",
                    image=image,
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
    )
    )

    return deployment
