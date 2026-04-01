import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Spain Top-50 Playlist Lifecycle Dashboard",
    page_icon="🎵",
    layout="wide"
)

# -----------------------------
# CUSTOM CSS
# -----------------------------
st.markdown("""
<style>
    .main {
        background-color: #0f172a;
        color: white;
    }

    h1, h2, h3, h4, h5, h6, p, label {
        color: white !important;
    }

    .hero-box {
        background: linear-gradient(135deg, #111827, #1e293b);
        padding: 28px;
        border-radius: 22px;
        border: 1px solid #334155;
        margin-bottom: 22px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }

    .kpi-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        padding: 20px;
        border-radius: 18px;
        border: 1px solid #334155;
        text-align: center;
        box-shadow: 0 6px 20px rgba(0,0,0,0.2);
    }

    .insight-box {
        background-color: #111827;
        padding: 22px;
        border-radius: 18px;
        border-left: 5px solid #38bdf8;
        margin-top: 12px;
        margin-bottom: 20px;
    }

    .chart-box {
        background-color: #111827;
        padding: 20px;
        border-radius: 18px;
        border: 1px solid #334155;
        margin-bottom: 20px;
        box-shadow: 0 6px 20px rgba(0,0,0,0.18);
    }

    .chart-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 14px;
        color: white;
    }

    .footer-box {
        text-align: center;
        color: #94a3b8;
        font-size: 14px;
        padding-top: 25px;
        padding-bottom: 10px;
    }

    section[data-testid="stSidebar"] {
        background-color: #111827;
    }

    div[data-testid="metric-container"] {
        background-color: transparent;
        border: none;
        box-shadow: none;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("spotify_spain_top50_cleaned.csv")
    lifecycle = pd.read_csv("spotify_spain_lifecycle.csv")

    df['date'] = pd.to_datetime(df['date'])
    lifecycle['entry_date'] = pd.to_datetime(lifecycle['entry_date'])
    lifecycle['exit_date'] = pd.to_datetime(lifecycle['exit_date'])
    lifecycle['peak_date'] = pd.to_datetime(lifecycle['peak_date'])

    return df, lifecycle

df, lifecycle = load_data()

# -----------------------------
# LIFECYCLE STAGE CLASSIFICATION
# -----------------------------
def classify_stage(row):
    if row['days_on_playlist'] <= 7:
        return "New Entry"
    elif row['peak_position'] <= 10 and row['entry_to_peak_days'] <= 7:
        return "Peak"
    elif row['days_on_playlist'] <= 30:
        return "Growth"
    elif row['days_on_playlist'] <= 90:
        return "Mature"
    else:
        return "Decline"

lifecycle['lifecycle_stage'] = lifecycle.apply(classify_stage, axis=1)

# -----------------------------
# HERO SECTION
# -----------------------------
st.markdown("""
<div class="hero-box">
    <h1>🎵 Spain Top-50 Playlist Lifecycle Dashboard</h1>
    <p style="font-size:18px; color:#cbd5e1;">
        Explore how songs enter, peak, survive, and exit Spain’s Top-50 playlist.
        Analyze retention, churn, lifecycle stages, and release strategy performance.
    </p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.title("🔍 Filters")

min_date = df['date'].min().date()
max_date = df['date'].max().date()

date_range = st.sidebar.date_input(
    "Select Date Range",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

explicit_filter = st.sidebar.selectbox(
    "Explicit Content",
    ["All", "Explicit Only", "Clean Only"]
)

album_filter = st.sidebar.selectbox(
    "Album Type",
    ["All", "single", "album"]
)

stage_filter = st.sidebar.selectbox(
    "Lifecycle Stage",
    ["All"] + sorted(lifecycle['lifecycle_stage'].dropna().unique().tolist())
)

# -----------------------------
# APPLY FILTERS
# -----------------------------
filtered_df = df.copy()

if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df = filtered_df[
        (filtered_df['date'] >= start_date) &
        (filtered_df['date'] <= end_date)
    ]

if explicit_filter == "Explicit Only":
    filtered_df = filtered_df[filtered_df['is_explicit'] == True]
elif explicit_filter == "Clean Only":
    filtered_df = filtered_df[filtered_df['is_explicit'] == False]

if album_filter != "All":
    filtered_df = filtered_df[filtered_df['album_type'] == album_filter]

filtered_song_ids = filtered_df['song_id'].unique()
filtered_lifecycle = lifecycle[lifecycle['song_id'].isin(filtered_song_ids)].copy()

if stage_filter != "All":
    filtered_lifecycle = filtered_lifecycle[filtered_lifecycle['lifecycle_stage'] == stage_filter]
    filtered_df = filtered_df[filtered_df['song_id'].isin(filtered_lifecycle['song_id'])]

# -----------------------------
# HANDLE EMPTY FILTER CASE
# -----------------------------
if filtered_df.empty or filtered_lifecycle.empty:
    st.warning("No data available for the selected filters. Try changing the filter values.")
    st.stop()

# -----------------------------
# KPI CALCULATIONS
# -----------------------------
avg_days = round(filtered_lifecycle['days_on_playlist'].mean(), 2)
avg_entry_peak = round(filtered_lifecycle['entry_to_peak_days'].mean(), 2)
avg_peak_position = round(filtered_lifecycle['peak_position'].mean(), 2)
stability = round(filtered_df.groupby('song_id')['position'].std().mean(), 2)

dates = sorted(filtered_df['date'].unique())
entries = []
exits = []

for i in range(1, len(dates)):
    prev = set(filtered_df[filtered_df['date'] == dates[i-1]]['song_id'])
    curr = set(filtered_df[filtered_df['date'] == dates[i]]['song_id'])
    entries.append(len(curr - prev))
    exits.append(len(prev - curr))

avg_churn = round((sum(entries) + sum(exits)) / (2 * len(entries)), 2) if len(entries) > 0 else 0

clean_avg = filtered_lifecycle[filtered_lifecycle['is_explicit'] == False]['days_on_playlist'].mean()
explicit_avg = filtered_lifecycle[filtered_lifecycle['is_explicit'] == True]['days_on_playlist'].mean()

single_avg = filtered_lifecycle[filtered_lifecycle['album_type'] == 'single']['days_on_playlist'].mean()
album_avg = filtered_lifecycle[filtered_lifecycle['album_type'] == 'album']['days_on_playlist'].mean()

# -----------------------------
# SIDEBAR QUICK STATS
# -----------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📌 Quick Stats")
st.sidebar.write(f"**Rows:** {filtered_df.shape[0]:,}")
st.sidebar.write(f"**Unique Songs:** {filtered_df['song_id'].nunique():,}")
st.sidebar.write(f"**Unique Artists:** {filtered_df['artist'].nunique():,}")
st.sidebar.write(f"**Date Range:** {filtered_df['date'].min().date()} → {filtered_df['date'].max().date()}")

# -----------------------------
# KPI DISPLAY
# -----------------------------
st.subheader("📊 KPI Overview")

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f'<div class="kpi-card"><h4>Avg Days on Playlist</h4><h2>{avg_days}</h2></div>', unsafe_allow_html=True)
with k2:
    st.markdown(f'<div class="kpi-card"><h4>Entry-to-Peak Time</h4><h2>{avg_entry_peak}</h2></div>', unsafe_allow_html=True)
with k3:
    st.markdown(f'<div class="kpi-card"><h4>Churn Rate</h4><h2>{avg_churn}</h2></div>', unsafe_allow_html=True)
with k4:
    st.markdown(f'<div class="kpi-card"><h4>Stability Index</h4><h2>{stability}</h2></div>', unsafe_allow_html=True)
with k5:
    st.markdown(f'<div class="kpi-card"><h4>Avg Peak Position</h4><h2>{avg_peak_position}</h2></div>', unsafe_allow_html=True)

# -----------------------------
# SONG SEARCH PANEL
# -----------------------------
st.subheader("🔎 Song Search Explorer")

song_options = sorted(filtered_lifecycle['song_id'].unique().tolist())
selected_song = st.selectbox("Search for a Song", ["Select a song"] + song_options)

if selected_song != "Select a song":
    song_data = filtered_lifecycle[filtered_lifecycle['song_id'] == selected_song].iloc[0]

    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Entry Date", str(song_data['entry_date'].date()))
    s2.metric("Exit Date", str(song_data['exit_date'].date()))
    s3.metric("Peak Position", int(song_data['peak_position']))
    s4.metric("Days on Playlist", int(song_data['days_on_playlist']))
    s5.metric("Lifecycle Stage", song_data['lifecycle_stage'])

# -----------------------------
# INSIGHTS SECTION
# -----------------------------
st.subheader("🧠 Key Business Insights")

st.markdown(f"""
<div class="insight-box">
    <ul style="font-size:17px; line-height:1.9; color:#e2e8f0;">
        <li><b>Average song lifespan</b> is <b>{avg_days:.2f} days</b></li>
        <li>Songs reach their best position in around <b>{avg_entry_peak:.2f} days</b></li>
        <li>Playlist churn is approximately <b>{avg_churn:.2f} songs/day</b></li>
        <li><b>Clean songs</b> average <b>{clean_avg:.2f} days</b>, while <b>explicit songs</b> average <b>{explicit_avg:.2f} days</b></li>
        <li><b>Singles</b> average <b>{single_avg:.2f} days</b>, while <b>album tracks</b> average <b>{album_avg:.2f} days</b></li>
    </ul>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# CHARTS SECTION
# -----------------------------
st.subheader("📈 Interactive Visual Analytics")

# Row 1
c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="chart-box"><div class="chart-title">Top 10 Artists</div>', unsafe_allow_html=True)
    top_artists = filtered_df['artist'].value_counts().head(10).reset_index()
    top_artists.columns = ['artist', 'count']
    fig = px.bar(top_artists, x='artist', y='count', template="plotly_dark")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="chart-box"><div class="chart-title">Song Duration Distribution</div>', unsafe_allow_html=True)
    fig = px.histogram(filtered_df, x='duration_min', nbins=30, template="plotly_dark")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Row 2
c3, c4 = st.columns(2)

with c3:
    st.markdown('<div class="chart-box"><div class="chart-title">Explicit vs Clean Songs</div>', unsafe_allow_html=True)
    explicit_counts = filtered_df['is_explicit'].value_counts().reset_index()
    explicit_counts.columns = ['is_explicit', 'count']
    explicit_counts['is_explicit'] = explicit_counts['is_explicit'].map({True: 'Explicit', False: 'Clean'})
    fig = px.pie(explicit_counts, names='is_explicit', values='count', template="plotly_dark", hole=0.45)
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c4:
    st.markdown('<div class="chart-box"><div class="chart-title">Single vs Album Songs</div>', unsafe_allow_html=True)
    album_counts = filtered_df['album_type'].value_counts().reset_index()
    album_counts.columns = ['album_type', 'count']
    fig = px.bar(album_counts, x='album_type', y='count', template="plotly_dark")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Row 3
c5, c6 = st.columns(2)

with c5:
    st.markdown('<div class="chart-box"><div class="chart-title">Song Lifespan Distribution</div>', unsafe_allow_html=True)
    fig = px.histogram(filtered_lifecycle, x='days_on_playlist', nbins=30, template="plotly_dark")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c6:
    st.markdown('<div class="chart-box"><div class="chart-title">Playlist Churn Over Time</div>', unsafe_allow_html=True)
    if len(dates) > 1:
        churn_df = pd.DataFrame({'date': dates[1:], 'Entries': entries, 'Exits': exits})
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=churn_df['date'], y=churn_df['Entries'], mode='lines', name='Entries'))
        fig.add_trace(go.Scatter(x=churn_df['date'], y=churn_df['Exits'], mode='lines', name='Exits'))
        fig.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# LIFECYCLE STAGE DISTRIBUTION
# -----------------------------
st.subheader("🔄 Lifecycle Stage Analysis")

lc1, lc2 = st.columns(2)

with lc1:
    st.markdown('<div class="chart-box"><div class="chart-title">Lifecycle Stage Distribution</div>', unsafe_allow_html=True)
    stage_counts = filtered_lifecycle['lifecycle_stage'].value_counts().reset_index()
    stage_counts.columns = ['lifecycle_stage', 'count']
    fig = px.bar(stage_counts, x='lifecycle_stage', y='count', template="plotly_dark")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with lc2:
    st.markdown('<div class="chart-box"><div class="chart-title">Average Days by Lifecycle Stage</div>', unsafe_allow_html=True)
    stage_days = filtered_lifecycle.groupby('lifecycle_stage')['days_on_playlist'].mean().reset_index()
    fig = px.bar(stage_days, x='lifecycle_stage', y='days_on_playlist', template="plotly_dark")
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# TOP SONG TABLES
# -----------------------------
st.subheader("🏆 Top Performing Tracks")

t1, t2 = st.columns(2)

with t1:
    st.markdown('<div class="chart-box"><div class="chart-title">Longest Lasting Songs</div>', unsafe_allow_html=True)
    longest_songs = filtered_lifecycle.sort_values(by='days_on_playlist', ascending=False).head(10)[
        ['song_id', 'days_on_playlist', 'peak_position', 'lifecycle_stage']
    ]
    st.dataframe(longest_songs, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with t2:
    st.markdown('<div class="chart-box"><div class="chart-title">Most Stable Songs</div>', unsafe_allow_html=True)
    stability_df = filtered_df.groupby('song_id')['position'].std().reset_index()
    stability_df.columns = ['song_id', 'position_std']
    stable_songs = stability_df.sort_values(by='position_std').head(10)
    st.dataframe(stable_songs, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# RECOMMENDATION PANEL
# -----------------------------
st.subheader("💼 Strategic Recommendations")

st.markdown("""
<div class="insight-box">
    <ul style="font-size:17px; line-height:1.9; color:#e2e8f0;">
        <li>Prioritize <b>single releases</b> for stronger playlist retention</li>
        <li>Focus promotion during the <b>first 10 days</b> after chart entry</li>
        <li>Monitor high-churn periods for <b>competitive release timing</b></li>
        <li>Use lifecycle stages to identify <b>high-growth and long-tail hit songs</b></li>
        <li>Balance <b>clean vs explicit releases</b> depending on audience targeting</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# DOWNLOAD BUTTON
# -----------------------------
st.subheader("⬇️ Export Data")

csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Filtered Dataset as CSV",
    data=csv,
    file_name="filtered_spain_playlist_data.csv",
    mime="text/csv"
)

# -----------------------------
# DATA PREVIEW
# -----------------------------
st.subheader("📄 Filtered Dataset Preview")
st.dataframe(filtered_df.head(50), use_container_width=True)

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("""
<div class="footer-box">
    Developed as part of the Spain Top-50 Playlist Lifecycle Analysis Project using Streamlit + Plotly.
</div>
""", unsafe_allow_html=True)