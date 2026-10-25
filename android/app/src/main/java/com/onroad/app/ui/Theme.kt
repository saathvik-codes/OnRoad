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
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.NumberFormat
import java.util.Locale

/** OnRoad colours. Light follows CarDekho / Cars24-style clean white surfaces; dark is the original "night drive". */
data class OnRoadColors(val night: Color, val panel: Color, val panel2: Color, val line: Color, val mute: Color, val ink: Color,
                        val ignition: Color, val electric: Color, val good: Color, val amber: Color, val dark: Boolean)

val LightColors = OnRoadColors(night = Color(0xFFF4F5F8), panel = Color(0xFFFFFFFF), panel2 = Color(0xFFEDEFF4), line = Color(0xFFE2E5EC),
    mute = Color(0xFF5E6778), ink = Color(0xFF111522), ignition = Color(0xFFF2441F), electric = Color(0xFF0B7FC1),
    good = Color(0xFF0E9F55), amber = Color(0xFFB86E00), dark = false)
val DarkColors = OnRoadColors(night = Color(0xFF05060A), panel = Color(0xFF0E1119), panel2 = Color(0xFF161A26), line = Color(0xFF232838),
    mute = Color(0xFF94A3B8), ink = Color(0xFFF1F4FA), ignition = Color(0xFFFF4D2E), electric = Color(0xFF39D0FF),
    good = Color(0xFF34D399), amber = Color(0xFFFFB547), dark = true)
/** The palette in use; snapshot state, so every screen and drawing redraws when the theme changes. */
object Pal { var c by androidx.compose.runtime.mutableStateOf(LightColors) }

// the names every screen already uses; they now follow the phone's light / dark setting
val Night: Color get() = Pal.c.night
val Panel: Color get() = Pal.c.panel
val Panel2: Color get() = Pal.c.panel2
val Line: Color get() = Pal.c.line
val Mute: Color get() = Pal.c.mute
val Ink: Color get() = Pal.c.ink
val Ignition: Color get() = Pal.c.ignition
val Electric: Color get() = Pal.c.electric
val Good: Color get() = Pal.c.good
val Amber: Color get() = Pal.c.amber
val IsDark: Boolean get() = Pal.c.dark
val IgnitionGradient = Brush.linearGradient(listOf(Color(0xFFFFB347), Color(0xFFFF4D2E), Color(0xFFC2185B)))

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
fun OnRoadTheme(content: @Composable () -> Unit) {
    val mode by ThemeMode.mode.collectAsState()           // "system" | "light" | "dark", picked in Profile
    val c = when (mode) { "dark" -> DarkColors; "light" -> LightColors
        else -> if (androidx.compose.foundation.isSystemInDarkTheme()) DarkColors else LightColors }
    if (Pal.c != c) Pal.c = c
    // status / navigation bar icons dark on light, light on dark, also when the theme is switched in Profile
    val view = androidx.compose.ui.platform.LocalView.current
    if (!view.isInEditMode) androidx.compose.runtime.SideEffect {
        (view.context as? android.app.Activity)?.window?.let { w ->
            androidx.core.view.WindowCompat.getInsetsController(w, view).apply {
                isAppearanceLightStatusBars = !c.dark; isAppearanceLightNavigationBars = !c.dark
            }
        }
    }
    val scheme = if (c.dark) darkColorScheme(primary = c.ignition, onPrimary = Color.White, secondary = c.electric, background = c.night,
        onBackground = c.ink, surface = c.panel, onSurface = c.ink, surfaceVariant = c.panel2, onSurfaceVariant = c.mute, outline = c.line,
        surfaceContainer = c.panel, surfaceContainerLow = c.night, surfaceContainerHigh = c.panel2, error = Color(0xFFFF5C7A))
    else androidx.compose.material3.lightColorScheme(primary = c.ignition, onPrimary = Color.White, secondary = c.electric, background = c.night,
        onBackground = c.ink, surface = c.panel, onSurface = c.ink, surfaceVariant = c.panel2, onSurfaceVariant = c.mute, outline = c.line,
        surfaceContainer = c.panel, surfaceContainerLow = c.night, surfaceContainerHigh = c.panel2, surfaceContainerHighest = c.panel2,
        error = Color(0xFFD92D4B))
    run {
        MaterialTheme(colorScheme = scheme, typography = Type) {
            // screens draw on plain Boxes/Columns, not Surfaces, so set the default text/icon colour here
            CompositionLocalProvider(LocalContentColor provides c.ink, LocalTextStyle provides Type.bodyLarge, content = content)
        }
    }
}

/** Rounded panel used for every card. */
@Composable
fun Tile(modifier: Modifier = Modifier, pad: Int = 16, content: @Composable BoxScope.() -> Unit) = Box(
    // light: white card with a soft shadow (like the big Indian car apps); dark: bordered panel
    (if (IsDark) modifier else modifier.shadow(3.dp, RoundedCornerShape(20.dp), ambientColor = Color(0x22111522), spotColor = Color(0x22111522)))
        .clip(RoundedCornerShape(20.dp)).background(Panel).border(1.dp, Line, RoundedCornerShape(20.dp)).padding(pad.dp),
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


/** The user's theme choice, saved on the phone. */
object ThemeMode {
    private var prefs: android.content.SharedPreferences? = null
    val mode = kotlinx.coroutines.flow.MutableStateFlow("system")
    fun init(ctx: android.content.Context) {
        prefs = ctx.getSharedPreferences("onroad_theme", android.content.Context.MODE_PRIVATE)
        mode.value = prefs?.getString("mode", "system") ?: "system"
    }
    fun set(m: String) { mode.value = m; prefs?.edit()?.putString("mode", m)?.apply() }
}
