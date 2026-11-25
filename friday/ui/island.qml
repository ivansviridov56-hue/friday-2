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

            Item {
                id: blob
                readonly property int base: index * 5
                readonly property real sw: backend.iconData[base + 2] || 0
                readonly property real sh: backend.iconData[base + 3] || 0
                width: sw
                height: sh
                x: (backend.iconData[base] || 0) - sw / 2
                y: (backend.iconData[base + 1] || 0) - sh / 2

                Rectangle {
                    anchors.fill: parent
                    visible: !backend.iconSoft
                    radius: backend.iconData[blob.base + 4] || 0
                    color: backend.dotColor
                }

                Shape {
                    anchors.fill: parent
                    visible: backend.iconSoft
                    preferredRendererType: Shape.GeometryRenderer

                    ShapePath {
                        strokeColor: "transparent"
                        startX: 0
                        startY: 0
                        fillGradient: RadialGradient {
                            centerX: blob.sw / 2
                            centerY: blob.sh / 2
                            centerRadius: blob.sw / 2
                            focalX: blob.sw / 2
                            focalY: blob.sh / 2
                            GradientStop { position: 0.0; color: Qt.alpha(backend.dotColor, 0.9) }
                            GradientStop { position: 0.55; color: Qt.alpha(backend.dotColor, 0.35) }
                            GradientStop { position: 1.0; color: Qt.alpha(backend.dotColor, 0.0) }
                        }
                        PathLine { x: blob.sw; y: 0 }
                        PathLine { x: blob.sw; y: blob.sh }
                        PathLine { x: 0; y: blob.sh }
                        PathLine { x: 0; y: 0 }
                    }
                }
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