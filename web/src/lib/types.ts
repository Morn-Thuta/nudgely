export type Customer = {
  id: string;
  channel: string;
  name: string | null;
  label: string;
  uplift: number | null;
  p_no_msg: number | null;
  handover: boolean;
  opted_out: boolean;
  last_seen_at: string;
  created_at: string;
};
export type Message = {
  id: number;
  customer_id: string;
  sender: "customer" | "store";
  text: string;
  handover: boolean;
  created_at: string;
};
export type Tag = {
  id: number;
  customer_id: string;
  type: string;
  value: string;
  evidence: string;
  created_at: string;
};
export type Draft = {
  customer_id: string;
  message: string;
  tags_used: string[];
  reason: string;
};
export type Dataset = {
  customers: Customer[];
  messages: Message[];
  tags: Tag[];
};
