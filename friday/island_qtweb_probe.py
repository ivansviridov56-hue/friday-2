"""Probe: the island as a transparent Qt window with a web page inside (experiment, not wired in).

Run: python -m friday.island_qtweb_probe
The window ignores the mouse and the keyboard; it closes by itself after 60 s, or press Ctrl+C
in the console.
"""

from __future__ import annotations

import signal
import sys
import os

from PySide6.QtCore import QCoreApplication, Qt, QTimer, QUrl
from PySide6.QtGui import QColor
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication

WIDTH, HEIGHT = 480, 90

HTML = r"""<!doctype html>
<meta charset="utf-8">
<style>html,body{margin:0;background:transparent;overflow:hidden}canvas{display:block}</style>
<canvas id="c"></canvas>
<script>
const W=480,H=90,CAP_W=150,EXP_W=440,CAP_H=34,FLARE=10,R=14,PAD=9,LINE=17,TL=40,TR=18;
const TEXT="Привет, босс. Расскажу про космос: он большой, холодный и очень тихий, а звёзды вокруг нас светят уже миллиарды лет. Свет от некоторых из них идёт до нас дольше, чем существует человечество, и мы видим их такими, какими они были давным-давно.";
const words=TEXT.split(' ');
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
  const T=cycle%14;
  const open=T>1&&T<11;
  const shown=T<1.5?0:Math.min(words.length,Math.floor((T-1.5)/0.14));
  p=Math.max(0,Math.min(1,p+(open?dt:-dt)/0.45));
  const e=smooth(p);
  const lines=wrap(shown);
  const widest=lines.reduce((m,s)=>Math.max(m,g.measureText(s).width),0);
  const tW=shown>0?Math.max(CAP_W,Math.min(EXP_W,widest+TL+TR)):CAP_W;
  const tLH=shown>0?Math.max(LINE,Math.min(lines.length,2)*LINE):LINE;
  const tScroll=Math.max(0,lines.length-2)*LINE;
  openW=ease(openW,tW,dt,14);openLH=ease(openLH,tLH,dt,14);scroll=ease(scroll,tScroll,dt,10);
  phase+=dt*1.2;
  const h=q(CAP_H,Math.max(CAP_H,openLH+2*PAD),e),bodyW=q(CAP_W,openW,e);
  g.clearRect(0,0,W,H);
  const x0=(W-(bodyW+2*FLARE))/2,left=x0+FLARE,right=left+bodyW;
  g.beginPath();
  g.moveTo(x0,0);g.quadraticCurveTo(left,0,left,FLARE);g.lineTo(left,h-R);
  g.quadraticCurveTo(left,h,left+R,h);
  for(let x=left+R;x<right-R;x+=3){
    const u=(x-(left+R))/(bodyW-2*R);
    g.lineTo(x,h+1.6*Math.sin(Math.PI*u)*Math.sin(u*9.4+phase));
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
  if(now-fpsT>=1000){console.log('FPS '+frames);frames=0;fpsT=now;}
  setTimeout(()=>frame(performance.now()),0);
}
setTimeout(()=>frame(performance.now()),0);
</script>"""


class _Page(QWebEnginePage):
    """Prints the frame counter that the page writes to its console."""

    def javaScriptConsoleMessage(
        self, level, message, line, source
    ) -> None:  # noqa: N802
        if message.startswith("FPS "):
            print(f"island qtweb fps: {message[4:]}", flush=True)


def main() -> None:
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--disable-frame-rate-limit")
    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)
    app = QApplication(sys.argv)

    view = QWebEngineView()
    view.setWindowFlags(
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
        | Qt.WindowType.Tool
        | Qt.WindowType.WindowDoesNotAcceptFocus
        | Qt.WindowType.WindowTransparentForInput
    )
    view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    view.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    view.setStyleSheet("background: transparent;")
    page = _Page(view)
    page.setBackgroundColor(QColor(0, 0, 0, 0))
    view.setPage(page)
    page.setHtml(HTML, QUrl("about:blank"))

    screen = app.primaryScreen().geometry()
    view.setGeometry(
        screen.x() + (screen.width() - WIDTH) // 2, screen.y(), WIDTH, HEIGHT
    )
    view.show()

    signal.signal(signal.SIGINT, lambda *_: app.quit())
    keepalive = QTimer()  # lets Python see Ctrl+C while Qt is running
    keepalive.timeout.connect(lambda: None)
    keepalive.start(200)
    QTimer.singleShot(60_000, app.quit)
    app.exec()


if __name__ == "__main__":
    main()
