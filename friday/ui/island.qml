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

    Item {
        x: backend.dotX
        y: backend.bodyH / 2

        Repeater {
            model: backend.iconCount

            Rectangle {
                readonly property int base: index * 5
                readonly property real sw: backend.iconData[base + 2] || 0
                readonly property real sh: backend.iconData[base + 3] || 0
                width: sw
                height: sh
                x: (backend.iconData[base] || 0) - sw / 2
                y: (backend.iconData[base + 1] || 0) - sh / 2
                radius: backend.iconData[base + 4] || 0
                color: backend.dotColor
            }
        }
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