// Emits SQL for the fictional demo only. Run against a fresh project after migrations.
import fs from "node:fs";
const demo = JSON.parse(
  fs.readFileSync(new URL("../src/data/demo.json", import.meta.url), "utf8"),
);
const literal = (value) =>
  "'" + JSON.stringify(value).replaceAll("'", "''") + "'::jsonb";
const customers = demo.customers;
const messages = demo.messages.map((m) => ({
  customer_id: m.customer_id,
  sender: m.sender,
  text: m.text,
  handover: m.handover,
  created_at: m.created_at,
}));
const tags = demo.tags.map((t) => ({
  customer_id: t.customer_id,
  type: t.type,
  value: t.value,
  evidence: t.evidence,
  created_at: t.created_at,
}));
const sql = `begin;
insert into public.customers (id,channel,name,label,uplift,p_no_msg,handover,opted_out,created_at,last_seen_at)
select id,channel,name,label,uplift,p_no_msg,handover,opted_out,created_at,last_seen_at from jsonb_to_recordset(${literal(customers)}) as c(id text,channel text,name text,label text,uplift real,p_no_msg real,handover boolean,opted_out boolean,created_at timestamptz,last_seen_at timestamptz)
on conflict (id) do nothing;
insert into public.messages (customer_id,sender,text,handover,created_at)
select m.customer_id,m.sender,m.text,m.handover,m.created_at from jsonb_to_recordset(${literal(messages)}) as m(customer_id text,sender text,text text,handover boolean,created_at timestamptz)
where not exists (select 1 from public.messages old where old.customer_id=m.customer_id and old.text=m.text and old.sender=m.sender and old.created_at=m.created_at);
insert into public.tags (customer_id,type,value,evidence,created_at)
select customer_id,type,value,evidence,created_at from jsonb_to_recordset(${literal(tags)}) as t(customer_id text,type text,value text,evidence text,created_at timestamptz)
on conflict (customer_id,type,value) do nothing;
commit;`;
process.stdout.write(sql);
