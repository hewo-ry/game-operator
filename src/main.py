import kopf
import kubernetes

from templating import Protocol
from templating.deployment import DeploymentConfig
from templating.games.minecraft import MinecraftServerConfig, MinecraftServerSecrets
from templating.pvc import PersistentVolumeClaim
from templating.service import NodePort, Service
from utils import check_required_fields
from utils.minecraft import minecraft_server_create_fields


@kopf.on.create("hellshade.fi", "v1", "minecraftservers")
@kopf.on.resume("hellshade.fi", "v1", "minecraftservers")
def create_fn(spec, name, namespace, logger, **kwargs):
    # Parameter checks
    check_required_fields(spec, minecraft_server_create_fields)

    core_api = kubernetes.client.CoreV1Api()
    apps_api = kubernetes.client.AppsV1Api()

    data_pvc_name = f"{name}-data"
    config_map_name = f"{name}-config"
    secret_name = f"{name}-secret"
    service_name = f"{name}-svc"
    deployment_name = name

    common_labels = {"app": name}

    pvcs = core_api.list_namespaced_persistent_volume_claim(namespace=namespace)

    pvc_names = [pvc.metadata.name for pvc in pvcs.items]

    if data_pvc_name not in pvc_names:
        # Templating
        data_pvc = PersistentVolumeClaim.from_spec(spec.get("storage")).to_pvc(
            data_pvc_name, namespace, common_labels
        )
        logger.debug(f"PVC={data_pvc}")

        kopf.adopt(data_pvc)

        obj_pvc = core_api.create_namespaced_persistent_volume_claim(
            namespace=namespace, body=data_pvc
        )
        logger.info(f"PVC {obj_pvc.metadata.name} created in namespace {namespace}.")

        data_pvc_name = obj_pvc.metadata.name

    config_maps = core_api.list_namespaced_config_map(namespace=namespace)

    config_map_names = [cm.metadata.name for cm in config_maps.items]

    if config_map_name not in config_map_names:
        data_config_map = MinecraftServerConfig.from_spec(
            spec.get("serverConfig")
        ).to_config_map(config_map_name, namespace, common_labels)
        logger.debug(f"ConfigMap={data_config_map}")

        kopf.adopt(data_config_map)

        obj_config_map = core_api.create_namespaced_config_map(
            namespace=namespace, body=data_config_map
        )
        logger.info(
            f"ConfigMap {obj_config_map.metadata.name} created in namespace {namespace}."
        )

        config_map_name = obj_config_map.metadata.name

    secrets = core_api.list_namespaced_secret(namespace=namespace)

    secret_names = [secret.metadata.name for secret in secrets.items]

    if secret_name not in secret_names:
        data_secrets = MinecraftServerSecrets().to_secret(
            secret_name, namespace, common_labels
        )
        logger.debug(f"Secret={data_secrets}")

        kopf.adopt(data_secrets)

        obj_secrets = core_api.create_namespaced_secret(
            namespace=namespace, body=data_secrets
        )
        logger.info(
            f"Secret {obj_secrets.metadata.name} created in namespace {namespace}."
        )

        secret_name = obj_secrets.metadata.name

    services = core_api.list_namespaced_service(namespace=namespace)

    service_names = [service.metadata.name for service in services.items]

    if service_name not in service_names:
        data_service = Service(
            ports=[
                NodePort("minecraft", 25565, Protocol.TCP, "minecraft"),
                NodePort("query", 25565, Protocol.UDP, "query"),
            ]
        ).to_service(service_name, namespace, name)
        logger.debug(f"Service={data_service}")

        kopf.adopt(data_service)

        obj_service = core_api.create_namespaced_service(
            namespace=namespace, body=data_service
        )
        logger.info(
            f"Service {obj_service.metadata.name} created in namespace {namespace}."
        )

        service_name = obj_service.metadata.name

    deployments = apps_api.list_namespaced_deployment(namespace=namespace)

    deployment_names = [deployment.metadata.name for deployment in deployments.items]

    if deployment_name not in deployment_names:
        data_deployment = DeploymentConfig.from_spec(
            name, namespace, spec.get("serverConfig")
        ).to_deployment(common_labels)
        logger.debug(f"Deployment={data_deployment}")

        kopf.adopt(data_deployment)

        obj_deployment = apps_api.create_namespaced_deployment(
            namespace=namespace, body=data_deployment
        )
        logger.info(
            f"Deployment {obj_deployment.metadata.name} created in namespace {namespace}."
        )

        deployment_name = obj_deployment.metadata.name

    return {
        "data-pvc-name": data_pvc_name,
        "config-name": config_map_name,
        "secret-name": secret_name,
        "deployment-name": deployment_name,
    }


@kopf.on.update("hellshade.fi", "v1", "minecraftservers")
def update_fn(spec, status, name, namespace, logger, **kwargs):
    storage_size = spec.get("storageSize")
    if not storage_size:
        raise kopf.PermanentError(f"StorageSize is required, got: {storage_size!r}.")

    pvc_name = status["create_fn"]["data-pvc-name"]
    pvc_patch = {"spec": {"resources": {"requests": {"storage": storage_size}}}}

    api = kubernetes.client.CoreV1Api()
    obj = api.patch_namespaced_persistent_volume_claim(
        namespace=namespace,
        name=pvc_name,
        body=pvc_patch,
    )

    logger.info(f"PVC {obj.metadata.name} updated in namespace {namespace}.")


@kopf.on.field("hellshade.fi", "v1", "minecraftservers", field="metadata.labels")
def relabel(diff, status, namespace, logger, **kwargs):
    labels_patch = {field[0]: new for op, field, old, new in diff}
    pvc_name = status["create_fn"]["data-pvc-name"]
    config_map_name = status["create_fn"]["config-name"]
    secret_name = status["create_fn"]["secret-name"]
    patch = {"metadata": {"labels": labels_patch}}

    api = kubernetes.client.CoreV1Api()
    pvc_obj = api.patch_namespaced_persistent_volume_claim(
        namespace=namespace,
        name=pvc_name,
        body=patch,
    )
    logger.info(f"PVC {pvc_obj.metadata.name} labels updated in namespace {namespace}.")
    config_map_obj = api.patch_namespaced_config_map(
        namespace=namespace, name=config_map_name, body=patch
    )
    logger.info(
        f"ConfigMap {config_map_obj.metadata.name} labels updated in namespace {namespace}."
    )
    secret_obj = api.patch_namespaced_secret(
        namespace=namespace, name=secret_name, body=patch
    )
    logger.info(
        f"Secret {secret_obj.metadata.name} labels updated in namespace {namespace}."
    )
