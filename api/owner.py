"""The shop owner's API: /api/owner/... (nudgely/shops.py does the work).

Every call needs the owner's Supabase sign-in token. Any signed-in account can own one shop;
the team role is not needed. Each request is scoped to the caller's own shop, so one shop can
never read or change another's customers.

Local development without Supabase: set NUDGELY_DEV_AUTH=1 and send `Bearer dev-<anything>`.
That bypass refuses to run when Supabase is configured, so it can't open up a real deployment.
"""

import base64
import binascii
import os

import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from nudgely import shops, supabase_sync

router = APIRouter(prefix="/api/owner")


def owner_id(request: Request):
    auth = request.headers.get("authorization", "")
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
    if not token:
        raise HTTPException(401, "Sign in first.")
    if not supabase_sync.enabled():
        if os.getenv("NUDGELY_DEV_AUTH") == "1" and token.startswith("dev-") and len(token) <= 64:
            return token
        raise HTTPException(503, "Sign-in isn't set up on this server.")
    url, key = supabase_sync._config()
    try:
        r = requests.get(f"{url}/auth/v1/user", timeout=10, headers={"apikey": key, "Authorization": auth})
    except requests.RequestException:
        raise HTTPException(503, "Couldn't check your sign-in. Try again.")
    user = r.json() if r.ok else {}
    if not user.get("id"):
        raise HTTPException(401, "Your sign-in has expired. Sign in again.")
    return user["id"]


def _call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except shops.ShopError as e:
        raise HTTPException(e.status, str(e))


def _decode(data_base64):
    try:
        return base64.b64decode(data_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(400, "The file didn't arrive intact. Try uploading it again.")


class ShopIn(BaseModel):
    name: str = Field(..., max_length=80)


class WhatsAppIn(BaseModel):
    wa_token: str | None = Field(None, max_length=1000)
    wa_phone_number_id: str | None = Field(None, max_length=40)
    template_name: str | None = Field(None, max_length=80)
    template_language: str | None = Field(None, max_length=10)


class SettingsIn(BaseModel):
    offer: str | None = Field(None, max_length=200)
    note: str | None = Field(None, max_length=400)
    whatsapp: WhatsAppIn | None = None


class FileIn(BaseModel):
    filename: str = Field("sales.csv", max_length=120)
    data_base64: str = Field(..., min_length=4, max_length=2_800_000)


class PlanIn(BaseModel):
    size: int | None = Field(None, ge=1, le=5000)
    holdout_pct: int = Field(shops.HOLD_DEFAULT, ge=0, le=50)


class RowIn(BaseModel):
    blank: str | None = Field(None, max_length=400)
    approved: bool | None = None


class SendIn(BaseModel):
    live: bool = False


@router.get("/shop")
def get_shop(request: Request):
    return {"shop": shops.shop_view(owner_id(request))}


@router.post("/shop")
def create_shop(body: ShopIn, request: Request):
    return {"shop": _call(shops.create_shop, owner_id(request), body.name)}


@router.post("/settings")
def settings(body: SettingsIn, request: Request):
    wa = body.whatsapp.model_dump(exclude_none=True) if body.whatsapp else None
    return {"shop": _call(shops.update_settings, owner_id(request), body.offer, body.note, wa)}


@router.post("/sales")
def sales(body: FileIn, request: Request):
    return _call(shops.save_sales, owner_id(request), _decode(body.data_base64), body.filename)


@router.get("/customers")
def customers(request: Request):
    return {"customers": _call(shops.list_customers, owner_id(request))}


@router.get("/campaigns")
def campaigns(request: Request):
    return {"campaigns": _call(shops.list_campaigns, owner_id(request))}


@router.post("/campaigns")
def plan(body: PlanIn, request: Request):
    return _call(shops.plan_campaign, owner_id(request), body.size, body.holdout_pct)


@router.get("/campaigns/{cid}")
def campaign(cid: str, request: Request):
    return _call(shops.campaign_view, owner_id(request), cid)


@router.post("/campaigns/{cid}/write")
def write(cid: str, request: Request):
    return _call(shops.write_messages, owner_id(request), cid)


@router.post("/campaigns/{cid}/rows/{row_id}")
def edit(cid: str, row_id: str, body: RowIn, request: Request):
    return _call(shops.edit_row, owner_id(request), cid, row_id, body.blank, body.approved)


@router.post("/campaigns/{cid}/approve-all")
def approve(cid: str, request: Request):
    return _call(shops.approve_all, owner_id(request), cid)


@router.post("/campaigns/{cid}/send")
def send(cid: str, body: SendIn, request: Request):
    return _call(shops.send_campaign, owner_id(request), cid, body.live)


@router.post("/campaigns/{cid}/returns")
def returns_upload(cid: str, body: FileIn, request: Request):
    return _call(shops.record_returns, owner_id(request), cid, _decode(body.data_base64), body.filename)
