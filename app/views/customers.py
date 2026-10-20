import streamlit as st

from lib import LABEL_HELP, example_data_note, header, load_customers, top_tag

header("Customers", "Kampung Fresh customers, scored by how much a message changes their chance to come back.")
example_data_note("customers.csv", "tags.json")

df = load_customers().copy()
df["top_tag"] = df["customer_id"].map(top_tag)

cols = st.columns(3)
for col, label in zip(cols, ["Persuadable", "Sure Thing", "Lost Cause"]):
    col.metric(label, int((df.label == label).sum()), help=LABEL_HELP[label])

labels = st.multiselect("Filter by label", ["Persuadable", "Sure Thing", "Lost Cause"],
                        default=["Persuadable", "Sure Thing", "Lost Cause"])
view = df[df.label.isin(labels)].reset_index(drop=True)
table = view.assign(uplift=view.uplift * 100, p_no_msg=view.p_no_msg * 100)

event = st.dataframe(
    table[["name", "label", "uplift", "p_no_msg", "days_since_last_visit", "top_tag"]],
    hide_index=True,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "name": "Customer",
        "label": "Label",
        "uplift": st.column_config.ProgressColumn("Uplift", format="+%.1f%%", min_value=0,
                                                  max_value=float(max(df.uplift.max(), 0.01)) * 100,
                                                  help="Extra chance to return if messaged"),
        "p_no_msg": st.column_config.NumberColumn("Return anyway", format="%.0f%%",
                                                  help="Chance to return with no message"),
        "days_since_last_visit": st.column_config.NumberColumn("Days since visit"),
        "top_tag": "Top tag from chats",
    },
)
st.caption("Click a row to open that customer.")

if event.selection.rows:
    st.session_state["customer_id"] = view.iloc[event.selection.rows[0]]["customer_id"]
    st.switch_page("views/customer_detail.py")
