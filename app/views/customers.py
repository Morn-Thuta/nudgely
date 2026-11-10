import streamlit as st

from lib import badge, example_data_note, header, load_customers, messages, tags, top_tag

header("People, not just profiles.", "Everyone in your shop, scored by how much a message would change them.")
example_data_note("customers.csv", "tags.json")

df = load_customers().copy()
df["top_tag"] = df["customer_id"].map(top_tag)
drafts, extractions = messages(), tags()

cols = st.columns(4)
cols[0].metric("Customers", len(df))
for col, label in zip(cols[1:], ["Persuadable", "Sure Thing", "Lost Cause"]):
    col.metric(label, int((df.label == label).sum()))  # explained in the line below, so no tooltip
st.markdown(
    "<div style='font-size:0.9em;line-height:2;margin:-4px 0 6px'>"
    + " ".join(f"<span style='display:inline-block;margin-right:18px'>{badge(label)} {text}</span>"
               for label, text in (
        ("Persuadable", "a message changes their mind - message these"),
        ("Sure Thing", "coming back anyway - save the message"),
        ("Lost Cause", "a message will not change it - save the message")))
    + "</div>", unsafe_allow_html=True)
st.caption(f"{sum(cid in extractions for cid in df.customer_id)} have chats on file · "
           f"{sum(cid in drafts for cid in df.customer_id)} have a message written · "
           "names and chats are made up; the scores come from a model trained on real grocery data")

search = st.text_input("Find a customer", placeholder="Search by ID, name or chat topic…")
labels = st.multiselect("Show", ["Persuadable", "Sure Thing", "Lost Cause"],
                        default=["Persuadable", "Sure Thing", "Lost Cause"])
view = df[df.label.isin(labels)].reset_index(drop=True)
if search:
    view = view[view['name'].str.contains(search, case=False, regex=False) | view.customer_id.str.contains(search, case=False, regex=False) | view.top_tag.str.contains(search, case=False, regex=False)].reset_index(drop=True)
st.caption(f"{len(view)} customers · the ones a message changes most come first · click a row to open that customer")
table = view.assign(uplift=view.uplift * 100, p_no_msg=view.p_no_msg * 100)

event = st.dataframe(
    table[["customer_id", "name", "label", "uplift", "p_no_msg", "days_since_last_visit", "top_tag"]],
    hide_index=True,
    width="stretch",
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "customer_id": "ID",
        "name": "Customer",
        "label": "Type",
        "uplift": st.column_config.ProgressColumn("Change if messaged", format="+%.1f%%", min_value=0,
                                                  max_value=float(max(df.uplift.max(), 0.01)) * 100,
                                                  help="How much more likely they are to come back if you "
                                                       "message them. This is what the ranking is built on."),
        "p_no_msg": st.column_config.NumberColumn("Coming back anyway", format="%.0f%%",
                                                  help="Their chance of coming back if you send nothing"),
        "days_since_last_visit": st.column_config.NumberColumn("Days since visit"),
        "top_tag": "What their chats say",
    },
)

if event.selection.rows:
    st.session_state["customer_id"] = view.iloc[event.selection.rows[0]]["customer_id"]
    st.switch_page("views/customer_detail.py")

if st.button("Plan a campaign for these customers →", type="primary"):
    st.switch_page("views/campaign.py")
