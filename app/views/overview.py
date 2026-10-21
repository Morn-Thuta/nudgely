import plotly.graph_objects as go
import streamlit as st
from lib import BRAND, header, summary, load_customers, messages, tags
from design import customer_row

header('Your next connection starts here.', 'Turn customer conversations into thoughtful reasons to come back.')
st.markdown('''<div class="hero"><div style="flex:1.7"><div class="eyebrow">SMALL MESSAGES. MEANINGFUL RETURNS.</div><h1>Bring them back.<br>Make it personal.</h1><p>Find the customers a message could make a difference to. Remember what matters to them. Give every conversation a thoughtful next step.</p><span class="pill">Built for your neighbourhood business</span></div><div class="hero-side"><div style="color:#D6E5D9;font-size:12px">KAMPUNG FRESH · EXAMPLE PREVIEW</div><div class="bubble">Hi Aisha! Following up on your oat milk request. Would you like us to check availability for you?<br><br><small>Reply STOP to opt out</small></div><div style="color:#ADC7BA;font-size:11px">A relevant memory. A more personal message.</div></div></div>''', unsafe_allow_html=True)
a,b = st.columns([1,3])
if a.button('Build a campaign →', type='primary', width='stretch'):
    st.switch_page('views/campaign.py')
if b.button('Explore your customers'):
    st.switch_page('views/customers.py')
df = load_customers()
drafts, extractions = messages(), tags()
st.markdown('<div class="section-label">Your workspace at a glance</div>', unsafe_allow_html=True)
a,b,c,d = st.columns(4)
a.metric('Customer profiles', len(df))
b.metric('High-uplift customers', int((df.label == 'Persuadable').sum()))
c.metric('Profiles with chat memory', sum(cid in extractions for cid in df.customer_id))
d.metric('Available message drafts', sum(cid in drafts for cid in df.customer_id))
st.caption('Fictional identities and chats · Lenta model scores · Drafts may include examples and require review.')
main,aside = st.columns([1.6,1], gap='large')
with main, st.container(border=True):
    st.subheader('A smarter place to start')
    st.caption('Historical Lenta experiment · Share of incremental visits captured')
    s = summary()
    if s:
        capture = s['top30_capture_share']
        fig = go.Figure(go.Bar(y=['Random selection','Nudgely targeting'], x=[.30,capture], orientation='h',marker_color=['#BCD5CE',BRAND],text=['30%',f'{capture:.0%}'],textposition='outside'))
        fig.update_layout(height=230,margin=dict(l=5,r=45,t=10,b=10),paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',xaxis=dict(tickformat='.0%',range=[0,max(.7,capture*1.2)]),yaxis=dict(autorange='reversed'),bargap=.5)
        st.plotly_chart(fig,width='stretch')
        st.caption('Top 30% by uplift score. Historical evidence, not results from a live Kampung Fresh campaign.')
        ci=s.get('top30_capture_ci90')
        if ci: st.caption(f'90% bootstrap interval: {ci[0]:.0%}–{ci[1]:.0%}. This estimate is noisy.')
    else:
        st.info('Historical model results are not available yet.')
with aside, st.container(border=True):
    st.subheader('Customers to get to know')
    st.caption('Highest estimated uplift · Not yet a send list')
    for _,row in df.head(4).iterrows():
        customer_row(row['name'],row.label,row.uplift)
st.markdown('<div class="section-label">From a conversation to a comeback</div>',unsafe_allow_html=True)
for col,number,title,copy in zip(st.columns(4),['01','02','03','04'],['Find your audience','Remember the details','Make it personal','Measure the difference'],['Start with customers whose return probability may improve with a message.','Use chat memories and quoted evidence to understand what matters.','Review every draft. Rehearse first, then send to opted-in test accounts.','Keep a no-message group and separate predictions from observed results.']):
    with col:
        st.markdown(f'<div class="feature"><div class="num">{number}</div><h3>{title}</h3><p>{copy}</p></div>',unsafe_allow_html=True)
