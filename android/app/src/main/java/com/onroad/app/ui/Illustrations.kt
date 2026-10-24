package com.onroad.app.ui

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.rotate

// Onboarding art, drawn in code so it stays crisp on every screen and matches the palette exactly.

@Composable
private fun floatAnim(): Float {
    val t = rememberInfiniteTransition(label = "float")
    val v by t.animateFloat(0f, 1f, infiniteRepeatable(tween(2200), RepeatMode.Reverse), label = "f")
    return v
}

private fun DrawScope.glow(c: Color, center: Offset, r: Float) =
    drawCircle(Brush.radialGradient(listOf(c.copy(alpha = 0.35f), Color.Transparent), center, r), r, center)

/** A car on the road with a price tag: "the real price". */
@Composable
fun PriceArt(modifier: Modifier = Modifier) {
    val f = floatAnim()
    Canvas(modifier.fillMaxWidth().aspectRatio(1.25f)) {
        val w = size.width; val h = size.height
        glow(Ignition, Offset(w * 0.5f, h * 0.55f), w * 0.55f)
        // road
        drawRoundRect(Panel2, Offset(w * 0.04f, h * 0.74f), Size(w * 0.92f, h * 0.08f), CornerRadius(h * 0.04f))
        for (i in 0 until 5) drawLine(Ink.copy(alpha = 0.5f), Offset(w * (0.12f + i * 0.18f), h * 0.78f), Offset(w * (0.2f + i * 0.18f), h * 0.78f), 4f, StrokeCap.Round)
        // car body
        val body = Path().apply {
            moveTo(w * 0.14f, h * 0.70f); lineTo(w * 0.14f, h * 0.58f)
            quadraticTo(w * 0.16f, h * 0.52f, w * 0.26f, h * 0.50f)
            lineTo(w * 0.36f, h * 0.40f); quadraticTo(w * 0.40f, h * 0.36f, w * 0.48f, h * 0.36f)
            lineTo(w * 0.62f, h * 0.36f); quadraticTo(w * 0.68f, h * 0.36f, w * 0.72f, h * 0.42f)
            lineTo(w * 0.78f, h * 0.50f); quadraticTo(w * 0.88f, h * 0.52f, w * 0.88f, h * 0.60f)
            lineTo(w * 0.88f, h * 0.70f); close()
        }
        drawPath(body, Brush.linearGradient(listOf(Color(0xFFFFB347), Ignition, Color(0xFFC2185B)), Offset(0f, h * 0.36f), Offset(w, h * 0.7f)))
        // windows
        val win = Path().apply {
            moveTo(w * 0.32f, h * 0.49f); lineTo(w * 0.40f, h * 0.41f); lineTo(w * 0.53f, h * 0.41f); lineTo(w * 0.53f, h * 0.49f); close()
            moveTo(w * 0.56f, h * 0.41f); lineTo(w * 0.66f, h * 0.41f); lineTo(w * 0.72f, h * 0.49f); lineTo(w * 0.56f, h * 0.49f); close()
        }
        drawPath(win, Night.copy(alpha = 0.75f))
        // wheels
        listOf(0.30f, 0.72f).forEach { x ->
            drawCircle(Night, h * 0.085f, Offset(w * x, h * 0.70f))
            drawCircle(Ink.copy(alpha = 0.85f), h * 0.04f, Offset(w * x, h * 0.70f))
        }
        drawCircle(Color(0xFFFFF3C4), h * 0.018f, Offset(w * 0.86f, h * 0.56f))          // headlamp
        // floating price tag
        val ty = h * (0.10f + 0.03f * f)
        rotate(-8f, Offset(w * 0.70f, ty + h * 0.1f)) {
            drawRoundRect(Ink, Offset(w * 0.56f, ty), Size(w * 0.30f, h * 0.17f), CornerRadius(h * 0.04f))
            drawCircle(Night, h * 0.018f, Offset(w * 0.60f, ty + h * 0.085f))
            drawRoundRect(Ignition, Offset(w * 0.64f, ty + h * 0.045f), Size(w * 0.17f, h * 0.03f), CornerRadius(8f))
            drawRoundRect(Mute, Offset(w * 0.64f, ty + h * 0.095f), Size(w * 0.11f, h * 0.025f), CornerRadius(8f))
        }
        drawLine(Mute, Offset(w * 0.62f, ty + h * 0.16f), Offset(w * 0.56f, h * 0.38f), 3f, StrokeCap.Round)
    }
}

/** An itemised receipt: "every rupee explained". */
@Composable
fun ReceiptArt(modifier: Modifier = Modifier) {
    val f = floatAnim()
    Canvas(modifier.fillMaxWidth().aspectRatio(1.25f)) {
        val w = size.width; val h = size.height
        glow(Electric, Offset(w * 0.5f, h * 0.5f), w * 0.55f)
        val left = w * 0.27f; val top = h * (0.08f + 0.02f * f); val rw = w * 0.46f; val rh = h * 0.80f
        // zig-zag bottom edge
        val paper = Path().apply {
            moveTo(left, top); lineTo(left + rw, top); lineTo(left + rw, top + rh)
            val teeth = 8; val step = rw / teeth
            for (i in 0 until teeth) { lineTo(left + rw - step * (i + 0.5f), top + rh - h * 0.03f); lineTo(left + rw - step * (i + 1), top + rh) }
            close()
        }
        drawPath(paper, Ink)
        drawRoundRect(Electric, Offset(left + rw * 0.12f, top + rh * 0.08f), Size(rw * 0.45f, h * 0.035f), CornerRadius(8f))
        val rows = listOf(0.62f, 0.48f, 0.55f, 0.40f, 0.50f)
        rows.forEachIndexed { i, len ->
            val y = top + rh * (0.24f + i * 0.11f)
            drawRoundRect(Mute.copy(alpha = 0.6f), Offset(left + rw * 0.12f, y), Size(rw * len * 0.8f, h * 0.022f), CornerRadius(6f))
            drawRoundRect(Night.copy(alpha = 0.7f), Offset(left + rw * 0.70f, y), Size(rw * 0.18f, h * 0.022f), CornerRadius(6f))
        }
        drawLine(Mute, Offset(left + rw * 0.1f, top + rh * 0.80f), Offset(left + rw * 0.9f, top + rh * 0.80f), 3f)
        drawRoundRect(Ignition, Offset(left + rw * 0.55f, top + rh * 0.84f), Size(rw * 0.33f, h * 0.035f), CornerRadius(8f))
        // "flagged" stamp
        val c = Offset(w * 0.76f, h * 0.30f)
        drawCircle(Good, h * 0.11f, c)
        drawPath(Path().apply { moveTo(c.x - h * 0.05f, c.y); lineTo(c.x - h * 0.01f, c.y + h * 0.04f); lineTo(c.x + h * 0.055f, c.y - h * 0.045f) },
            Night, style = Stroke(width = h * 0.022f, cap = StrokeCap.Round))
    }
}

/** A map with showroom pins around "you": "showrooms near you". */
@Composable
fun MapArt(modifier: Modifier = Modifier) {
    val f = floatAnim()
    Canvas(modifier.fillMaxWidth().aspectRatio(1.25f)) {
        val w = size.width; val h = size.height
        glow(Good, Offset(w * 0.5f, h * 0.5f), w * 0.55f)
        drawRoundRect(Panel, Offset(w * 0.08f, h * 0.08f), Size(w * 0.84f, h * 0.84f), CornerRadius(h * 0.08f))
        // roads
        val road = Panel2
        drawLine(road, Offset(w * 0.08f, h * 0.55f), Offset(w * 0.92f, h * 0.42f), h * 0.05f)
        drawLine(road, Offset(w * 0.40f, h * 0.08f), Offset(w * 0.55f, h * 0.92f), h * 0.05f)
        drawLine(road, Offset(w * 0.08f, h * 0.22f), Offset(w * 0.92f, h * 0.30f), h * 0.03f)
        // you + distance rings
        val me = Offset(w * 0.48f, h * 0.50f)
        drawCircle(Electric.copy(alpha = 0.18f + 0.1f * f), h * (0.20f + 0.03f * f), me)
        drawCircle(Electric, h * 0.035f, me); drawCircle(Ink, h * 0.015f, me)
        // pins
        listOf(Offset(w * 0.24f, h * 0.36f) to Ignition, Offset(w * 0.74f, h * 0.30f) to Amber, Offset(w * 0.70f, h * 0.72f) to Good).forEach { (p, c) ->
            val pin = Path().apply {
                moveTo(p.x, p.y + h * 0.10f)
                cubicTo(p.x - h * 0.09f, p.y + h * 0.01f, p.x - h * 0.06f, p.y - h * 0.08f, p.x, p.y - h * 0.08f)
                cubicTo(p.x + h * 0.06f, p.y - h * 0.08f, p.x + h * 0.09f, p.y + h * 0.01f, p.x, p.y + h * 0.10f)
            }
            drawPath(pin, c)
            drawCircle(Night, h * 0.022f, Offset(p.x, p.y - h * 0.015f))
        }
    }
}
