package com.onroad.app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.text.ExperimentalTextApi
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import com.onroad.app.R
import androidx.compose.material3.Text
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.NumberFormat
import java.util.Locale

// "Night drive" palette: matches the OnRoad web brand.
val Night = Color(0xFF05060A)
val Panel = Color(0xFF0E1119)
val Panel2 = Color(0xFF161A26)
val Line = Color(0xFF232838)
val Mute = Color(0xFF94A3B8)
val Ink = Color(0xFFF1F4FA)
val Ignition = Color(0xFFFF4D2E)
val Electric = Color(0xFF39D0FF)
val Good = Color(0xFF34D399)
val Amber = Color(0xFFFFB547)
val IgnitionGradient = Brush.linearGradient(listOf(Color(0xFFFFB347), Ignition, Color(0xFFC2185B)))

// Same type as the website: Space Grotesk for headings and prices, Geist for everything else (both SIL OFL, bundled).
@OptIn(ExperimentalTextApi::class)
private fun vf(res: Int, w: Int) = Font(res, FontWeight(w), variationSettings = FontVariation.Settings(FontVariation.weight(w)))
@OptIn(ExperimentalTextApi::class)
val Display = FontFamily(vf(R.font.space_grotesk, 500), vf(R.font.space_grotesk, 600), vf(R.font.space_grotesk, 700))
@OptIn(ExperimentalTextApi::class)
val Body = FontFamily(vf(R.font.geist, 400), vf(R.font.geist, 500), vf(R.font.geist, 600), vf(R.font.geist, 700))

private val Type = Typography(
    displaySmall = TextStyle(fontFamily = Display, fontWeight = FontWeight.Bold, fontSize = 32.sp, letterSpacing = (-1).sp, lineHeight = 37.sp),
    headlineMedium = TextStyle(fontFamily = Display, fontWeight = FontWeight.Bold, fontSize = 26.sp, letterSpacing = (-0.6).sp),
    headlineSmall = TextStyle(fontFamily = Display, fontWeight = FontWeight.Bold, fontSize = 22.sp, letterSpacing = (-0.4).sp),
    titleLarge = TextStyle(fontFamily = Display, fontWeight = FontWeight.Bold, fontSize = 19.sp, letterSpacing = (-0.2).sp),
    titleMedium = TextStyle(fontFamily = Body, fontWeight = FontWeight.SemiBold, fontSize = 16.sp),
    titleSmall = TextStyle(fontFamily = Body, fontWeight = FontWeight.SemiBold, fontSize = 14.sp),
    bodyLarge = TextStyle(fontFamily = Body, fontSize = 15.sp, lineHeight = 22.sp),
    bodyMedium = TextStyle(fontFamily = Body, fontSize = 14.sp, lineHeight = 20.sp),
    bodySmall = TextStyle(fontFamily = Body, fontSize = 12.sp, lineHeight = 16.sp),
    labelLarge = TextStyle(fontFamily = Body, fontWeight = FontWeight.SemiBold, fontSize = 14.sp),
    labelMedium = TextStyle(fontFamily = Body, fontWeight = FontWeight.Medium, fontSize = 12.sp),
    labelSmall = TextStyle(fontFamily = Body, fontWeight = FontWeight.SemiBold, fontSize = 11.sp, letterSpacing = 0.8.sp),
)

@Composable
fun OnRoadTheme(content: @Composable () -> Unit) = MaterialTheme(
    colorScheme = darkColorScheme(primary = Ignition, onPrimary = Color.White, secondary = Electric, background = Night,
        onBackground = Ink, surface = Panel, onSurface = Ink, surfaceVariant = Panel2, onSurfaceVariant = Mute, outline = Line,
        surfaceContainer = Panel, surfaceContainerLow = Night, surfaceContainerHigh = Panel2, error = Color(0xFFFF5C7A)),
    typography = Type,
) {
    // screens draw on plain Boxes/Columns, not Surfaces, so set the default text/icon colour here
    CompositionLocalProvider(LocalContentColor provides Ink, LocalTextStyle provides Type.bodyLarge, content = content)
}

/** Rounded panel used for every card. */
@Composable
fun Tile(modifier: Modifier = Modifier, pad: Int = 16, content: @Composable BoxScope.() -> Unit) = Box(
    modifier.clip(RoundedCornerShape(22.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(22.dp)).padding(pad.dp),
    content = content,
)

@Composable
fun Chip(text: String, color: Color = Mute, modifier: Modifier = Modifier) = Text(
    text, color = color, style = MaterialTheme.typography.labelSmall,
    modifier = modifier.clip(RoundedCornerShape(50)).background(color.copy(alpha = 0.12f)).padding(horizontal = 10.dp, vertical = 5.dp),
)

private val inr = NumberFormat.getNumberInstance(Locale("en", "IN"))
fun rupees(n: Long?) = if (n == null) "—" else "₹" + inr.format(n)
fun lakh(n: Long?): String = when {
    n == null -> "Price on request"
    n >= 10_000_000 -> "₹%.2f Cr".format(n / 1e7).replace(".00", "")
    else -> "₹%.2f L".format(n / 1e5).replace(".00", "")
}
fun range(a: Long?, b: Long?) = if (a == null) "Price on request" else if (b == null || b == a) lakh(a) else "${lakh(a)} – ${lakh(b).removePrefix("₹")}"
