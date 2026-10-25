package com.onroad.app.ui

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.CompositingStrategy
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.graphics.drawscope.rotate
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.rememberTextMeasurer
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlin.math.roundToInt

private val Smooth = CubicBezierEasing(0.22f, 1f, 0.36f, 1f)        // fast in, long gentle settle
private val Glide = CubicBezierEasing(0.65f, 0f, 0.35f, 1f)

/** The OnRoad mark: the gradient ring (a wheel / a road loop) with a lane cutting through it, as on the app icon. */
private fun androidx.compose.ui.graphics.drawscope.DrawScope.mark(sweep: Float, lane: Float, laneShift: Float, bg: Color, dash: Color) {
    val stroke = size.minDimension * 0.25f
    val inset = stroke / 2
    val ring = Brush.linearGradient(listOf(Color(0xFFFFB347), Color(0xFFFF4D2E), Color(0xFFC2185B)), Offset.Zero, Offset(size.width, size.height))
    drawArc(ring, startAngle = -200f, sweepAngle = 360f * sweep, useCenter = false, topLeft = Offset(inset, inset),
        size = Size(size.width - stroke, size.height - stroke), style = Stroke(stroke, cap = StrokeCap.Butt))
    if (lane <= 0f) return
    rotate(-24f) {
        // the road cutting through the ring, then its lane markings moving like passing headlights
        val h = size.height * 0.12f * lane
        drawRect(bg, Offset(-size.width * 0.1f, center.y - h / 2), Size(size.width * 1.2f, h))
        val dashW = size.width * 0.12f
        val gap = size.width * 0.13f
        var x = -size.width * 0.1f + (laneShift % (dashW + gap))
        while (x < size.width * 1.1f) {
            drawLine(dash.copy(alpha = lane), Offset(x, center.y), Offset(x + dashW, center.y), strokeWidth = size.height * 0.035f, cap = StrokeCap.Round)
            x += dashW + gap
        }
    }
}

/**
 * Launch animation, about 1.8 s: the ring draws itself, a lane races through it, the ring settles into the "o" of the
 * wordmark while "nroad" unrolls out of it, a light streak crosses the word, then everything fades into the app.
 * Tap to skip; skipped entirely when the phone has animations turned off.
 */
@Composable
fun BrandIntro(onDone: () -> Unit) {
    val ctx = androidx.compose.ui.platform.LocalContext.current
    val noMotion = remember {
        android.provider.Settings.Global.getFloat(ctx.contentResolver, android.provider.Settings.Global.ANIMATOR_DURATION_SCALE, 1f) == 0f
    }
    // Android 12+ has just shown the ring as its launch icon at nearly this size: continue from it instead of redrawing
    val draw = remember { Animatable(if (android.os.Build.VERSION.SDK_INT >= 31) 1f else 0f) }      // ring sweep
    val lane = remember { Animatable(if (android.os.Build.VERSION.SDK_INT >= 31) 1f else 0f) }   // the road through the ring (on the launch icon too)
    val drive = remember { Animatable(0f) }     // lane markings move
    val settle = remember { Animatable(0f) }    // ring moves into the wordmark
    val reveal = remember { Animatable(0f) }    // "nroad" unrolls
    val shine = remember { Animatable(-0.3f) }  // light streak position
    val tag = remember { Animatable(0f) }       // tagline
    val out = remember { Animatable(1f) }       // whole screen fade

    LaunchedEffect(Unit) {
        if (noMotion) { onDone(); return@LaunchedEffect }
        coroutineScope {
            // ~1.4 s, like the big Indian apps: one beat of motion, a clean logo, then straight into the app
            if (draw.value < 1f) { draw.animateTo(1f, tween(480, easing = Smooth)); lane.animateTo(1f, tween(160)) }
            drive.animateTo(0.45f, tween(320, easing = LinearEasing))                 // the lane races through once
            val a = async { lane.animateTo(0f, tween(260)) }                          // ...and dissolves: a clean "o"
            val b = async { drive.animateTo(0.75f, tween(260, easing = LinearEasing)) }
            val c = async { settle.animateTo(1f, tween(520, easing = Glide)) }        // the ring becomes the "o"
            delay(180)
            reveal.animateTo(1f, tween(420, easing = Smooth))                         // "nroad" unrolls out of it
            a.await(); b.await(); c.await()
            val d = async { shine.animateTo(1.3f, tween(420, easing = LinearEasing)) }
            tag.animateTo(1f, tween(260))
            d.await()
            delay(120)
            out.animateTo(0f, tween(220))
        }
        onDone()
    }

    val bg = Night
    val ink = Ink
    val density = LocalDensity.current
    val wordStyle = TextStyle(fontFamily = Display, fontWeight = FontWeight.Bold, fontSize = 46.sp, letterSpacing = (-1.5).sp)
    val measurer = rememberTextMeasurer()
    val wordWidth = remember(wordStyle) { measurer.measure("nroad", wordStyle).size.width }
    val markSize = 28.dp
    val gapPx = with(density) { 3.dp.toPx() }
    val markPx = with(density) { markSize.toPx() }
    // at rest the ring sits left of the word; at the start it is centred on screen and 2.6x larger
    val startShift = (wordWidth + gapPx) / 2f
    // starts at the size of the launch icon's ring (~100 dp), ends as a lowercase "o"
    val scale = 3.5f - 2.5f * settle.value

    Box(Modifier.fillMaxSize().background(bg).graphicsLayer { alpha = out.value }
        .clickable(remember { MutableInteractionSource() }, indication = null) { onDone() }, contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Canvas(Modifier.size(markSize)
                    .offset { IntOffset((startShift * (1 - settle.value)).roundToInt(), with(density) { 5.dp.roundToPx() }) }
                    .graphicsLayer { scaleX = scale; scaleY = scale }) {
                    mark(draw.value, lane.value, drive.value * size.width * 2.4f, bg, ink)
                }
                Spacer(Modifier.width(3.dp))
                // "nroad" unrolls out of the ring, with a light streak passing over it
                Text(buildAnnotatedString {
                    withStyle(SpanStyle(color = ink)) { append("n") }
                    withStyle(SpanStyle(color = Ignition)) { append("road") }
                }, style = wordStyle,
                    modifier = Modifier
                        .graphicsLayer { compositingStrategy = CompositingStrategy.Offscreen; alpha = if (reveal.value > 0f) 1f else 0f
                            translationX = -24.dp.toPx() * (1 - reveal.value) }
                        .drawWithContent {
                            clipRect(right = size.width * reveal.value) { this@drawWithContent.drawContent() }
                            val x = size.width * shine.value
                            drawRect(Brush.linearGradient(listOf(Color.Transparent, Color.White.copy(alpha = 0.55f), Color.Transparent),
                                Offset(x - size.width * 0.18f, 0f), Offset(x + size.width * 0.18f, size.height)),
                                blendMode = androidx.compose.ui.graphics.BlendMode.SrcAtop)
                        })
            }
            Spacer(Modifier.height(14.dp))
            Text("The real on-road price", style = TextStyle(fontFamily = Body, fontWeight = FontWeight.Medium, fontSize = 14.sp,
                letterSpacing = 0.6.sp), color = Mute, modifier = Modifier.graphicsLayer { alpha = tag.value; translationY = 8.dp.toPx() * (1 - tag.value) })
        }
    }
}
