"""Probe: the island as a transparent PyWebView window (experiment, not wired into the app).

Run: python -m friday.island_web_probe
Esc or a double click closes it; it also closes by itself after 90 s.
"""

from __future__ import annotations

import ctypes
import logging
import threading
import time

import webview

LOG = logging.getLogger("island_web_probe")
WIDTH, HEIGHT = 480, 90

HTML = r"""<!doctype html>
<meta charset="utf-8">
<style>html,body{margin:0;background:transparent;overflow:hidden}canvas{display:block}</style>
<canvas id="c"></canvas>
<script>
const W=480,H=90,CAP_W=150,EXP_W=440,CAP_H=34,FLARE=10,R=14,PAD=9,LINE=17,TL=40,TR=18;
const TEXT="Привет, босс. Расскажу про космос: он большой, холодный и очень тихий, а звёзды вокруг нас светят уже миллиарды лет. Свет от некоторых из них идёт до нас дольше, чем существует человечество, и мы видим их такими, какими они были давным-давно.";
const words=TEXT.split(' ');
const WORD_SEC=0.38,START=1.5,OPEN_END=START+words.length*WORD_SEC+1.5,CYCLE=OPEN_END+3;
const dpr=window.devicePixelRatio||1;
const cv=document.getElementById('c');
cv.width=W*dpr;cv.height=H*dpr;cv.style.width=W+'px';cv.style.height=H+'px';
const g=cv.getContext('2d');g.scale(dpr,dpr);
g.font='13px "Segoe UI", sans-serif';
g.textRendering='geometricPrecision';
const q=(a,b,k)=>a+(b-a)*k;
const ease=(v,t,dt,rate)=>{const d=t-v;if(Math.abs(d)<0.5)return t;const s=Math.max(Math.abs(d)*(1-Math.exp(-rate*dt)),30*dt);return v+Math.sign(d)*Math.min(s,Math.abs(d));};
const smooth=x=>x*x*(3-2*x);
let p=0,openW=CAP_W,openLH=LINE,scroll=0,phase=0,last=performance.now(),cycle=0,frames=0,fpsT=last;

function wrap(n){
  const maxW=EXP_W-TL-TR,out=[];let cur='';
  for(const w of words.slice(0,n)){
    const s=cur?cur+' '+w:w;
    if(g.measureText(s).width>maxW&&cur){out.push(cur);cur=w;}else cur=s;
  }
  if(cur)out.push(cur);
  return out;
}

function frame(now){
  const dt=Math.min((now-last)/1000,0.1);last=now;cycle+=dt;
  const T=cycle%CYCLE;
  const open=T>1&&T<OPEN_END;
  const shown=T<START?0:Math.min(words.length,Math.floor((T-START)/WORD_SEC));
  p=Math.max(0,Math.min(1,p+(open?dt:-dt)/0.45));
  const e=smooth(p);
  const lines=wrap(shown);
  const widest=lines.reduce((m,s)=>Math.max(m,g.measureText(s).width),0);
  const tW=shown>0?Math.max(CAP_W,Math.min(EXP_W,widest+TL+TR)):CAP_W;
  const tLH=shown>0?Math.max(LINE,Math.min(lines.length,2)*LINE):LINE;
  const tScroll=Math.max(0,lines.length-2)*LINE;
  openW=ease(openW,tW,dt,14);openLH=ease(openLH,tLH,dt,14);scroll=ease(scroll,tScroll,dt,10);
  phase+=dt*2.0;
  const h=q(CAP_H,Math.max(CAP_H,openLH+2*PAD),e),bodyW=q(CAP_W,openW,e);
  g.clearRect(0,0,W,H);
  const x0=(W-(bodyW+2*FLARE))/2,left=x0+FLARE,right=left+bodyW;
  g.beginPath();
  g.moveTo(x0,0);g.quadraticCurveTo(left,0,left,FLARE);g.lineTo(left,h-R);
  g.quadraticCurveTo(left,h,left+R,h);
  for(let x=left+R;x<right-R;x+=3){
    const u=(x-(left+R))/(bodyW-2*R);
    g.lineTo(x,h+3*Math.sin(Math.PI*u)*Math.sin(u*9.4+phase));
  }
  g.lineTo(right-R,h);g.quadraticCurveTo(right,h,right,h-R);g.lineTo(right,FLARE);
  g.quadraticCurveTo(right,0,right+FLARE,0);g.closePath();
  g.fillStyle='#202020';g.fill();
  g.fillStyle='#3aa6d8';g.beginPath();
  g.arc(q(W/2,left+22,e),h/2,5,0,Math.PI*2);g.fill();
  if(shown>0&&e>0.5){
    g.save();
    const top=(h-openLH)/2;
    g.beginPath();g.rect(left+TL,top,bodyW-TL-TR,openLH);g.clip();
    g.globalAlpha=Math.min(1,(e-0.5)*2);g.fillStyle='#e8e8e8';
    lines.forEach((s,i)=>g.fillText(s,left+TL,top+i*LINE-scroll+13));
    g.restore();
  }
  frames++;
  if(now-fpsT>=1000){
    try{pywebview.api.fps(frames);}catch(err){}
    frames=0;fpsT=now;
  }
  requestAnimationFrame(frame);
}
document.addEventListener('keydown',ev=>{if(ev.key==='Escape')pywebview.api.close();});
document.addEventListener('dblclick',()=>pywebview.api.close());
requestAnimationFrame(frame);
</script>"""


class Api:
    def close(self) -> None:
        for window in webview.windows:
            window.destroy()

    def fps(self, value: int) -> None:
        LOG.info("island web fps: %s", value)


class _AccentPolicy(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_int),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_int),
    ]


class _CompositionData(ctypes.Structure):
    _fields_ = [
        ("Attribute", ctypes.c_int),
        ("Data", ctypes.c_void_p),
        ("SizeOfData", ctypes.c_size_t),
    ]


class _Margins(ctypes.Structure):
    _fields_ = [(n, ctypes.c_int) for n in ("left", "right", "top", "bottom")]


def _extend_glass(title: str) -> bool:
    """Extend the glass over the whole window and ask for a fully clear gradient."""
    user32 = ctypes.windll.user32
    dwm = ctypes.windll.dwmapi
    user32.FindWindowW.restype = ctypes.c_void_p
    user32.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
    user32.SetWindowCompositionAttribute.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    dwm.DwmExtendFrameIntoClientArea.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    hwnd = user32.FindWindowW(None, title)
    if not hwnd:
        LOG.error("window handle not found")
        return False
    dwm.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(_Margins(-1, -1, -1, -1)))
    policy = _AccentPolicy(2, 2, 0, 0)  # ACCENT_ENABLE_TRANSPARENTGRADIENT, fully clear
    data = _CompositionData(
        19,  # WCA_ACCENT_POLICY
        ctypes.cast(ctypes.byref(policy), ctypes.c_void_p),
        ctypes.sizeof(policy),
    )
    return bool(user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data)))


def _make_form_transparent(window: object) -> None:
    """Paint the form black and extend the glass, so black is see-through."""
    try:
        from System import Action  # type: ignore[import-not-found]
        from System.Drawing import Color  # type: ignore[import-not-found]

        form = window.native  # type: ignore[attr-defined]

        def apply() -> None:
            form.TransparencyKey = Color.Empty
            form.BackColor = Color.Black

        for _ in range(2):  # the second pass catches a window that was not ready yet
            form.Invoke(Action(apply))
            _extend_glass("island probe")
            time.sleep(0.6)
    except Exception:
        LOG.exception("could not make the form transparent")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    screen_w = ctypes.windll.user32.GetSystemMetrics(0)
    window = webview.create_window(
        "island probe",
        html=HTML,
        width=WIDTH,
        height=HEIGHT,
        x=(screen_w - WIDTH) // 2,
        y=0,
        frameless=True,
        easy_drag=False,
        on_top=True,
        transparent=True,
        js_api=Api(),
    )

    def on_loaded() -> None:
        threading.Thread(
            target=_make_form_transparent, args=(window,), daemon=True
        ).start()

    window.events.loaded += on_loaded
    timer = threading.Timer(90, window.destroy)
    timer.daemon = True
    timer.start()
    webview.start()


if __name__ == "__main__":
    main()
