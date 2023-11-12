from typing import Optional
from fastapi import FastAPI
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from enum import Enum
import uvicorn

oauth2_scheme = HTTPBearer()

app = FastAPI()


class GenericOption(BaseModel):
    name: str
    value: Optional[str]
    vartype: str


class ExtensionData(BaseModel):
    control_data: dict[str, str]
    archive_path: str


class RemoteExtensionSpec(BaseModel):
    public_extensions: Optional[list[str]]
    custom_extensions: Optional[list[str]]
    library_index: dict[str, str]
    extension_data: dict[str, ExtensionData]


class Role(BaseModel):
    name: str
    encrypted_password: Optional[str]
    replication: Optional[bool]
    bypassrls: Optional[bool]
    options: list[GenericOption]


class Database(BaseModel):
    name: str
    owner: str
    options: list[GenericOption]
    restrict_conn: bool
    invalid: bool


class Cluster(BaseModel):
    cluster_id: Optional[str]
    name: Optional[str]
    state: Optional[str]
    roles: list[Role]
    databases: list[Database]
    postgresql_conf: Optional[str]
    settings: list[GenericOption]


class DeltaOperation(BaseModel):
    action: str
    name: str
    new_name: Optional[str]


class ComputeMode(Enum):
    primary = "Primary"
    replica = "Replica"
    static = "Static"


class ComputeSpec(BaseModel):
    format_version: float
    operation_uuid: str
    cluster: Cluster
    delta_operations: list[DeltaOperation]
    skip_pg_catalog_updates: bool
    tenant_id: str
    timeline_id: str
    pageserver_connstring: str
    safekeeper_connstrings: list[str]
    mode: ComputeMode
    storage_auth_token: str
    remote_extensions: list[RemoteExtensionSpec]


class ControlPlaneComputeStatus(Enum):
    Empty = "Empty"
    Attached = "Attached"


class ControlPlaneSpecResponse(BaseModel):
    spec: ComputeSpec
    status: ControlPlaneComputeStatus


class ReAttachRequest(BaseModel):
    node_id: str


class ReAttachResponseTenant(BaseModel):
    id: str
    gen: int


class ReAttachResponse(BaseModel):
    tenants: list[ReAttachResponseTenant]


class ValidateRequestTenant(BaseModel):
    id: str
    gen: int


class ValidateRequest(BaseModel):
    tenants: list[ValidateRequestTenant]


class ValidateResponseTenant(BaseModel):
    id: str
    valid: bool


class ValidateResponse(BaseModel):
    tenants: list[ValidateResponseTenant]


class AttachHookRequest(BaseModel):
    tenant_id: str
    node_id: str


class AttachHookResponse(BaseModel):
    gen: int


@app.get("/")
def read_root():
    return {"message": "Control Panel API is running"}


@app.post("/re-attach")
def re_attach(request: ReAttachRequest):
    tenants = []
    tenants.append(ReAttachResponseTenant(id=request.node_id, gen=1))
    response = ReAttachResponse(tenants=tenants)
    return response


@app.post("/validate")
def validate(request: ValidateRequest):
    tenants = []
    for tenant in request.tenants:
        # TODO: get tenant from k8s resources
        k8s_tenant = None
        valid = tenant.gen == k8s_tenant.gen
        tenants.append(ValidateResponseTenant(id=tenant.id, valid=valid))
    response = ValidateResponse(tenants=tenants)
    return response


@app.post("/attach-hook")
def attach_hook(request: AttachHookRequest):
    """
    Attach hook is called to attach a tenant to a page server to aqcuire a new generation number.
    """
    tenant_state = None  # TODO: get tenant_state from k8s resource
    # Check if tenant exists with tenant id i.e. request.tenant_id if not create it with gen=0 with page server id
    # i.e. request.node_id and save it
    if request.node_id != "":
        print(f'tenant_id: {request.tenant_id}, ps_id: {request.node_id}, generation: 1, issuing')
    elif tenant_state.pageserver != "":
        print(
            f'tenant_id: {request.tenant_id}, ps_id: {tenant_state.pageserver}, generation: {tenant_state.generation}, dropping')
    else:
        print(f'tenant_id: {request.tenant_id}, no-op: tenant already has no pageserver')

    response = AttachHookResponse(gen=1)
    return response


@app.get("/compute/api/v2/computes/{compute_id}/spec")
def get_compute_spec(compute_id: str) -> ControlPlaneSpecResponse:
    # TODO: get the compute deployment from k8s using compute_id
    response = ControlPlaneSpecResponse(
        spec=ComputeSpec(
            format_version=1.0,
            operation_uuid="",
            cluster=Cluster(
                cluster_id="",
                name="",
                state="",
                roles=[],
                databases=[],
                postgresql_conf="",
                settings=[]
            ),
            delta_operations=[],
            skip_pg_catalog_updates=False,
            tenant_id="",
            timeline_id="",
            pageserver_connstring="",
            safekeeper_connstrings=[
                ""
            ],
            mode=ComputeMode.primary,
            storage_auth_token="",
            remote_extensions=[]
        ),
        status=ControlPlaneComputeStatus.Empty
    )
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1234)
