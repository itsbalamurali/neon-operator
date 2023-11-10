import kubernetes

# Create CronJob for storage scrubber
def storage_scrubber_cronjob(
        namespace: str,
        image: str,
        schedule: str,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        bucket_name: str,
        bucket_region: str,
        bucket_endpoint: str,
) -> kubernetes.client.V1CronJob:
    return kubernetes.client.V1CronJob(
        api_version="batch/v1",
        kind="CronJob",
        metadata=kubernetes.client.V1ObjectMeta(
            name="storage-scrubber",
            namespace=namespace,
            labels={
                "app": "storage-scrubber",
            }
        ),
        spec=kubernetes.client.V1CronJobSpec(
            schedule=schedule,
            job_template=kubernetes.client.V1JobTemplateSpec(
                spec=kubernetes.client.V1JobSpec(
                    template=kubernetes.client.V1PodTemplateSpec(
                        spec=kubernetes.client.V1PodSpec(
                            restart_policy="OnFailure",
                            containers=[
                                kubernetes.client.V1Container(
                                    name="storage-scrubber",
                                    image=image,
                                    env=[
                                        kubernetes.client.V1EnvVar(
                                            name="AWS_ACCESS_KEY_ID",
                                            value_from=kubernetes.client.V1EnvVarSource(
                                                secret_key_ref=kubernetes.client.V1SecretKeySelector(
                                                    name="storage-credentials",
                                                    key="aws_access_key_id",
                                                )
                                            )
                                        ),
                                        kubernetes.client.V1EnvVar(
                                            name="AWS_SECRET_ACCESS_KEY",
                                            value_from=kubernetes.client.V1EnvVarSource(
                                                secret_key_ref=kubernetes.client.V1SecretKeySelector(
                                                    name="storage-credentials",
                                                    key="aws_secret_access_key",
                                                )
                                            )
                                        ),
                                        kubernetes.client.V1EnvVar(
                                            name="BUCKET_NAME",
                                            value=bucket_name,
                                        ),
                                        kubernetes.client.V1EnvVar(
                                            name="BUCKET_REGION",
                                            value=bucket_region,
                                        ),
                                        kubernetes.client.V1EnvVar(
                                            name="BUCKET_ENDPOINT",
                                            value=bucket_endpoint,
                                        ),
                                    ],
                                    command=[
                                        "echo",
                                        "storage-scrubber",
                                    ],
                                    volume_mounts=[
                                        kubernetes.client.V1VolumeMount(
                                            name="storage-credentials",
                                            mount_path="/etc/storage-credentials",
                                            read_only=True,
                                        )
                                    ],
                                )
                            ],
                            volumes=[
                                kubernetes.client.V1Volume(
                                    name="storage-credentials",
                                    secret=kubernetes.client.V1SecretVolumeSource(
                                        secret_name="storage-credentials",
                                    ),
                                )
                            ],
                        ),
                    ),
                ),
            ),
        ),
    )

