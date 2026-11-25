import QtQuick
import QtQuick.Shapes

Item {
    id: root

    FrameAnimation {
        running: true
        onTriggered: backend.frame(frameTime)
    }

    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.GeometryRenderer
        layer.enabled: true
        layer.samples: 4

        ShapePath {
            fillColor: backend.bodyColor
            strokeColor: "transparent"
            PathPolyline { path: backend.outline }
        }
        ShapePath {
            fillColor: "transparent"
            strokeColor: backend.lineColor
            strokeWidth: 1.2
            capStyle: ShapePath.RoundCap
            PathPolyline { path: backend.lightLine }
        }
    }

    Rectangle {
        readonly property real r: 5 + 1.5 * backend.pulse
        width: 2 * r
        height: 2 * r
        radius: r
        color: backend.dotColor
        x: backend.dotX - r
        y: backend.bodyH / 2 - r
    }

    Item {
        x: (root.width - backend.bodyW) / 2 + backend.textLeft
        y: (backend.bodyH - backend.linesH) / 2
        width: backend.bodyW - backend.textLeft - backend.textRight
        height: backend.linesH
        clip: true
        opacity: backend.textAlpha

        Text {
            y: -backend.scroll
            width: backend.wrapW
            wrapMode: Text.WordWrap
            textFormat: Text.StyledText
            color: backend.textColor
            font.pixelSize: 13
            font.family: backend.fontFamily
            text: backend.markup
        }
    }
}