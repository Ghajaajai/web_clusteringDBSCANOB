import streamlit as st
import pandas as pd
import pydeck as pdk
import os
os.environ["MAPBOX_API_KEY"] = "pk.eyJ1IjoiZ2hhemFhemhhciIsImEiOiJjbWsxbDdscHYwNWY3M2ZxNDF6c3UwanBvIn0.PrlIC3jEd60VnD3wTgIKBw"

# PAGE CONFIG
st.set_page_config(
    page_title="SIG Klasterisasi Bencana Jawa Barat",
    layout="wide"
)

# SESSION STATE
if "admin_logged_in" not in st.session_state:
    st.session_state.admin_logged_in = False

# HEADER
st.title("Sistem Informasi Geografis (SIG)")
st.subheader(
    "Klasterisasi Wilayah Rawan Bencana Alam di Kecamatan "
    "pada Kabupaten di Provinsi Jawa Barat"
)
st.markdown("---")

# ADMIN LOGIN
st.sidebar.header("Upload Data")

if not st.session_state.admin_logged_in:
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.admin_logged_in = True
            st.rerun()
        else:
            st.sidebar.error("Silahkan hubungi instansi")
else:
    st.sidebar.success("Login berhasil")
    if st.sidebar.button("Logout"):
        st.session_state.admin_logged_in = False
        st.rerun()

#DATA UPLOAD
DATA_DEFAULT = "hasil/data_sig_cluster_optimal.csv"

if st.session_state.admin_logged_in:
    st.sidebar.markdown("---")
    st.sidebar.header("📂 Manajemen Data")

    uploaded_file = st.sidebar.file_uploader(
        "Perbarui Data (CSV / XLSX)",
        type=["csv", "xlsx"]
    )

    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.sidebar.success("✅ Data berhasil diperbarui")
    else:
        df = pd.read_csv(DATA_DEFAULT)
else:
    df = pd.read_csv(DATA_DEFAULT)

#LOAD DATA
DATA_DEFAULT = "/data_sig_cluster_optimal.csv"
df = pd.read_csv(DATA_DEFAULT)

df["cluster"] = df["cluster"].astype(int)

#BENCANA DOMINAN
def bencana_dominan(row):
    data = {
        "Banjir": row["x1_banjir"],
        "Angin Puting Beliung": row["x2_angin"],
        "Gempa Bumi": row["x3_gempa"],
        "Tanah Longsor": row["x4_longsor"],
        "Kebakaran Hutan": row["x5_kebakaran"]
    }
    jenis = max(data, key=data.get)
    return jenis, data[jenis]

df[["bencana_dominan", "nilai_bencana_dominan"]] = df.apply(
    lambda r: pd.Series(bencana_dominan(r)), axis=1
)

# WARNA CLUSTER
COLOR_MAP = {
    0: [0, 200, 83],     # Hijau terang
    1: [41, 98, 255],    # Biru terang
    2: [255, 193, 7],    # Kuning terang
    3: [244, 67, 54],   # Merah terang
}

df["color"] = df["cluster"].apply(lambda x: COLOR_MAP.get(x, [160, 160, 160]))


# FILTER CLUSTER
st.sidebar.header("Filter Cluster")

cluster_selected = st.sidebar.multiselect(
    "Pilih Cluster",
    options=sorted(df["cluster"].unique()),
    default=sorted(df["cluster"].unique())
)

df_filtered = df[df["cluster"].isin(cluster_selected)]

def normalize_selected(obj):
    if isinstance(obj, list) and len(obj) > 0:
        return obj[0]
    if isinstance(obj, dict):
        return obj
    return None

# MITIGASI BENCANA (BERDASARKAN BENCANA DOMINAN)
MITIGASI_INFO = {
    "Banjir": {
        "aksi": [
            "Pembangunan tanggul dan tembok pertahanan sungai",
            "Pengaturan debit dan kecepatan aliran air",
            "Normalisasi sungai dan pembuatan sudetan"
        ],
        "sumber": "Ayu Sekar Ningrum (2020)"
    },
    "Gempa Bumi": {
        "aksi": [
            "Peningkatan ketahanan bangunan tahan gempa",
            "Penggunaan isolator seismik dan peredam getaran",
            "Edukasi masyarakat terkait evakuasi dan zona aman"
        ],
        "sumber": "Hasibuan"
    },
    "Tanah Longsor": {
        "aksi": [
            "Penguatan struktur dan bangunan penahan longsor",
            "Rekayasa konstruksi pada lereng rawan",
            "Pemasangan sistem peringatan dini curah hujan"
        ],
        "sumber": "Nofrohu (2024)"
    },
    "Angin Puting Beliung": {
        "aksi": [
            "Penguatan struktur bangunan dan infrastruktur lingkungan",
            "Penyediaan jalur evakuasi di wilayah rawan",
            "Pengadaan sistem peringatan dini dan pemangkasan pohon"
        ],
        "sumber": "Shofa (2025)"
    },
    "Kebakaran Hutan": {
        "aksi": [
            "Pengelolaan hutan secara menyeluruh",
            "Perbaikan akses jalan dan ketersediaan air",
            "Pelibatan masyarakat dalam penanganan kebakaran"
        ],
        "sumber": "Ermansyah (2024)"
    }
}

# DETAIL KECAMATAN (SIDEBAR)
st.sidebar.markdown("---")
st.sidebar.subheader("Detail Kecamatan")

selected_info = None

if "map" in st.session_state:
    selection = st.session_state["map"].get("selection", {})
    objects = selection.get("objects", {})

    if isinstance(objects, dict) and len(objects) > 0:
        selected_info = normalize_selected(list(objects.values())[0])
    elif isinstance(objects, list) and len(objects) > 0:
        selected_info = normalize_selected(objects[0])

if selected_info:
    st.sidebar.write(f"**Kabupaten:** {selected_info.get('kabupaten', '-')}")
    st.sidebar.write(f"**Kecamatan:** {selected_info.get('kecamatan', '-')}")
    st.sidebar.write(f"**Cluster:** {selected_info.get('cluster', '-')}")
    st.sidebar.write(f"**Bencana Dominan:** {selected_info.get('bencana_dominan', '-')}")
    st.sidebar.write(f"**Nilai Kejadian:** {selected_info.get('nilai_bencana_dominan', '-')}")
    st.sidebar.write("**Koordinat:**")
    st.sidebar.write(f"Lat: {selected_info.get('latitude', '-')}")
    st.sidebar.write(f"Lon: {selected_info.get('longitude', '-')}")

    # INFORMASI MITIGASI
    bencana = selected_info.get("bencana_dominan")
    if bencana in MITIGASI_INFO:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Rekomendasi Mitigasi")
        for aksi in MITIGASI_INFO[bencana]["aksi"]:
            st.sidebar.write(f"- {aksi}")
        st.sidebar.caption(f"Sumber: {MITIGASI_INFO[bencana]['sumber']}")
else:
    st.sidebar.info("Klik salah satu titik kecamatan pada peta")

# MAP
st.subheader("Peta Klasterisasi Kecamatan")

view_state = pdk.ViewState(
    latitude=df_filtered["latitude"].mean(),
    longitude=df_filtered["longitude"].mean(),
    zoom=8.5,
    pitch=50,
    bearing=-20
)

# GLOW LAYER (LUAR)
glow_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_filtered,
    get_position="[longitude, latitude]",
    get_radius=1200,
    radius_min_pixels=8,
    radius_max_pixels=24,
    get_fill_color="[color[0], color[1], color[2], 60]",
    stroked=False,
    pickable=False
)

# MAIN POINT LAYER (DALAM)
point_layer = pdk.Layer(
    "ScatterplotLayer",
    data=df_filtered,
    get_position="[longitude, latitude]",
    get_radius=300,
    radius_min_pixels=4,
    radius_max_pixels=10,
    get_fill_color="color",
    get_line_color=[255, 255, 255],
    line_width_min_pixels=1,
    pickable=True,
    auto_highlight=True
)

st.pydeck_chart(
    pdk.Deck(
        layers=[glow_layer, point_layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v11",
        tooltip={
            "html": """
            <b>Kecamatan:</b> {kecamatan}<br/>
            <b>Kabupaten:</b> {kabupaten}<br/>
            <b>Cluster:</b> {cluster}
            """,
            "style": {
                "backgroundColor": "#1e1e1e",
                "color": "white"
            }
        }
    ),
    on_select="rerun",
    key="map"
)
# RINGKASAN DATA
st.markdown("---")
st.subheader("Ringkasan Data")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Jumlah Kecamatan", len(df_filtered))
with col2:
    st.metric("Jumlah Cluster", df_filtered["cluster"].nunique())
with col3:
    st.metric("Metode Clustering:", "DBSCAN + Bayesian Optimization")

# FOOTER
st.markdown("""
---
**Tugas Akhir – Sistem Informasi Geografis**  
*Klasterisasi Wilayah Rawan Bencana Alam Provinsi Jawa Barat*  
DBSCAN + Bayesian Optimization
""")
