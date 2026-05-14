import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="藝素村探險放大鏡",
    layout="centered"
)

st.markdown(
    """
    <h1 style='text-align:center;'>
    🔍 藝素村探險放大鏡
    </h1>
    """,
    unsafe_allow_html=True
)

camera_html = """
<style>

body{
    margin:0;
    background:transparent;
    overflow:hidden;
}

/* 整個相機區域 */
.camera-wrap{
    position:relative;
    width:min(88vw, 340px);
    height:min(88vw, 340px);
    margin:auto;
    margin-top:20px;
}

/* 圓形鏡頭 */
video{
    width:100%;
    height:100%;
    border-radius:50%;
    object-fit:cover;

    border:10px solid #5d3a1f;

    box-shadow:
        0 0 35px rgba(0,0,0,0.55),
        inset 0 0 20px rgba(255,255,255,0.2);
}

/* 按鈕共用 */
.cam-btn{

    position:absolute;

    left:50%;
    transform:translateX(-50%);

    width:72px;
    height:72px;

    border-radius:50%;
    border:none;

    font-size:30px;
    cursor:pointer;

    z-index:9999;

    background: radial-gradient(
        circle at 35% 30%,
        #f0c9a6 0%,
        #c48c66 28%,
        #875030 68%,
        #472211 100%
    );

    box-shadow:
        inset 1px 1px 4px rgba(255,255,255,0.55),
        inset -3px -3px 8px rgba(0,0,0,0.75),
        0 0 0 4px #3d1f11,
        0 0 0 7px #916142,
        0 10px 18px rgba(0,0,0,0.65);

    transition:0.2s;
}

/* 按壓效果 */
.cam-btn:active{
    transform:translateX(-50%) scale(0.93);
}

/* 🔄 前後鏡頭切換 */
#switchBtn{
    top:calc(100% + 10px);
}

/* 📸 拍照 */
#captureBtn{
    top:calc(100% + 95px);
}

/* 手機優化 */
@media (max-width:768px){

    .cam-btn{
        width:68px;
        height:68px;
        font-size:28px;
    }

}

</style>

<div class="camera-wrap">

    <video
        id="video"
        autoplay
        playsinline
        muted
    ></video>

    <!-- 前後鏡頭切換 -->
    <button
        id="switchBtn"
        class="cam-btn"
    >
        🔄
    </button>

    <!-- 拍照 -->
    <button
        id="captureBtn"
        class="cam-btn"
    >
        📸
    </button>

</div>

<script>

let currentFacingMode = "environment";

const video = document.getElementById("video");

let currentStream = null;


/* 啟動相機 */
async function startCamera(){

    try{

        // 關閉舊鏡頭
        if(currentStream){
            currentStream.getTracks().forEach(
                track => track.stop()
            );
        }

        const stream =
            await navigator.mediaDevices.getUserMedia({

                video:{
                    facingMode: currentFacingMode
                },

                audio:false
            });

        currentStream = stream;

        video.srcObject = stream;

    }catch(err){

        alert(
            "無法開啟相機，請確認已允許相機權限"
        );

        console.error(err);
    }
}


/* 第一次啟動 */
startCamera();


/* 🔄 切換前後鏡頭 */
document
.getElementById("switchBtn")
.onclick = async ()=>{

    currentFacingMode =
        currentFacingMode === "environment"
        ? "user"
        : "environment";

    await startCamera();
};


/* 📸 拍照 */
document
.getElementById("captureBtn")
.onclick = ()=>{

    const canvas =
        document.createElement("canvas");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");

    ctx.drawImage(
        video,
        0,
        0,
        canvas.width,
        canvas.height
    );

    // 取得照片 base64
    const image =
        canvas.toDataURL("image/png");

    console.log(image);

    alert("📸 已拍攝！");
};

</script>
"""

components.html(
    camera_html,
    height=560
)
