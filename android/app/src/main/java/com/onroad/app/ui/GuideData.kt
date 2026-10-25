package com.onroad.app.ui

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.OpenInNew
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.KeyboardArrowDown
import androidx.compose.material.icons.outlined.KeyboardArrowUp
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

// Same text as the website's buying guide (onroad/web/src/app/buying-guide/page.tsx).
data class GuideStep(val title: String, val body: String, val docs: List<String> = emptyList(), val link: Pair<String, String>? = null)

val GUIDE = listOf(
    GuideStep("Compare the on-road price and get quotes", "Check the itemised on-road price for your city, then ask nearby showrooms for written quotes. Anything beyond road tax, registration, insurance, TCS and FASTag (handling, \"logistics\", forced accessories) is optional."),
    GuideStep("Book the car", "Pay the booking amount against a receipt that names the exact variant, colour, price and expected delivery date. Ask how the booking is refunded if you cancel."),
    GuideStep("Arrange the loan (if any)", "Get the bank's sanction letter before you pay the balance. The car is registered with the bank's lien (hypothecation), which adds a small fee.",
        listOf("PAN card", "Address proof", "Income proof (salary slips / ITR)", "Bank statements")),
    GuideStep("Buy insurance", "Third-party cover for 3 years is mandatory for new cars (5 years for two-wheelers). Own-damage cover can be bought from any insurer, not only the dealer's. Compare at least two quotes."),
    GuideStep("Pay and collect the invoice", "The tax invoice carries the ex-showroom price with GST. TCS (1% above ₹10 lakh) is collected here and can be claimed back in your income-tax return."),
    GuideStep("Registration at the RTO", "The dealer usually files registration on the government's Vahan system. You pay road tax and registration fees; the car gets a registration number, and the RC is issued (smart card in most states).",
        listOf("Form 20 (application)", "Form 21 (sale certificate from dealer)", "Form 22 (road-worthiness)", "Insurance certificate", "Address proof", "PAN or Form 60", "Form 34 if on loan"),
        "https://vahan.parivahan.gov.in/vahanservice/" to "Vahan citizen services"),
    GuideStep("High-security number plates and FASTag", "HSRP plates are fitted by the dealer (their cost is included in the vehicle price for new vehicles). Link a FASTag to the registration number before highway driving."),
    GuideStep("Delivery inspection", "Before you sign the delivery note, check the VIN and engine number against the invoice, the manufacturing month, odometer, paint and panels, and that every promised accessory is there."),
)

private fun doneSteps(ctx: Context): Set<String> = ctx.getSharedPreferences("onroad", Context.MODE_PRIVATE).getStringSet("guide_done", emptySet())!!
private fun saveDone(ctx: Context, s: Set<String>) = ctx.getSharedPreferences("onroad", Context.MODE_PRIVATE).edit().putStringSet("guide_done", s).apply()

/** Buying guide as a checklist: hero with progress, then a step timeline; tap a step to expand, tick it when done. */
@Composable
fun GuideScreen(onBack: () -> Unit) {
    val ctx = LocalContext.current
    var done by remember { mutableStateOf(doneSteps(ctx)) }
    var open by remember { mutableStateOf(0) }
    LazyColumn(Modifier.fillMaxSize(), contentPadding = PaddingValues(bottom = 28.dp)) {
        item {
            Box(Modifier.fillMaxWidth().background(Brush.verticalGradient(if (IsDark) listOf(Color(0xFF0E2A3A), Color(0xFF0B1424), Night) else listOf(Color(0xFFDDEFFB), Color(0xFFEAF4FB), Night)))
                .padding(start = 8.dp, end = 20.dp, top = 8.dp, bottom = 22.dp)) {
                Column {
                    IconButton(onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") }
                    Column(Modifier.padding(start = 12.dp)) {
                        Text("BUYING GUIDE", style = MaterialTheme.typography.labelSmall, color = Electric)
                        Spacer(Modifier.height(6.dp))
                        Text("From quote to\nnumber plate", style = MaterialTheme.typography.displaySmall)
                        Spacer(Modifier.height(8.dp))
                        Text("${GUIDE.size} steps every buyer in India goes through. Tick them off as you go.", color = Mute)
                        Art("hero-guide", Modifier.fillMaxWidth().height(170.dp).padding(top = 8.dp))
                        Spacer(Modifier.height(16.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            LinearProgressIndicator(progress = { done.size / GUIDE.size.toFloat() }, Modifier.weight(1f).height(8.dp).clip(RoundedCornerShape(50)),
                                color = Good, trackColor = Panel2)
                            Spacer(Modifier.width(12.dp))
                            Text("${done.size}/${GUIDE.size} done", style = MaterialTheme.typography.labelLarge, color = Good)
                        }
                    }
                }
            }
        }
        items(GUIDE.size) { i ->
            val g = GUIDE[i]
            val isDone = g.title in done
            val expanded = open == i
            Row(Modifier.fillMaxWidth().height(IntrinsicSize.Min).padding(horizontal = 16.dp)) {
                // timeline rail
                Column(Modifier.width(40.dp).fillMaxHeight(), horizontalAlignment = Alignment.CenterHorizontally) {
                    Box(Modifier.width(2.dp).height(10.dp).background(if (i == 0) Color.Transparent else Line))
                    Box(Modifier.size(32.dp).clip(CircleShape).background(if (isDone) Good else Panel2)
                        .border(2.dp, if (isDone) Good else if (expanded) Ignition else Line, CircleShape)
                        .clickable { done = if (isDone) done - g.title else done + g.title; saveDone(ctx, done) },
                        contentAlignment = Alignment.Center) {
                        if (isDone) Icon(Icons.Outlined.Check, "Done", tint = Color.White, modifier = Modifier.size(18.dp))
                        else Text("${i + 1}", fontWeight = FontWeight.Bold, color = if (expanded) Ignition else Ink)
                    }
                    Box(Modifier.width(2.dp).weight(1f).background(if (i == GUIDE.lastIndex) Color.Transparent else Line))
                }
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f).padding(vertical = 6.dp).clip(RoundedCornerShape(20.dp))
                    .background(if (expanded) Panel else Color.Transparent).border(1.dp, if (expanded) Line else Color.Transparent, RoundedCornerShape(20.dp))
                    .clickable { open = if (expanded) -1 else i }.padding(14.dp).animateContentSize()) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(g.title, style = MaterialTheme.typography.titleMedium, color = if (isDone) Mute else Ink, modifier = Modifier.weight(1f))
                        Icon(if (expanded) Icons.Outlined.KeyboardArrowUp else Icons.Outlined.KeyboardArrowDown, null, tint = Mute)
                    }
                    if (expanded) {
                        Spacer(Modifier.height(8.dp))
                        Text(g.body, color = Mute, style = MaterialTheme.typography.bodyMedium)
                        if (g.docs.isNotEmpty()) {
                            Spacer(Modifier.height(12.dp))
                            Text("DOCUMENTS TO CARRY", style = MaterialTheme.typography.labelSmall, color = Amber)
                            Spacer(Modifier.height(8.dp))
                            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                g.docs.forEach { d ->
                                    Row(Modifier.clip(Corner).background(Amber.copy(alpha = 0.10f)).padding(horizontal = 10.dp, vertical = 6.dp),
                                        verticalAlignment = Alignment.CenterVertically) {
                                        Icon(Icons.Outlined.Description, null, tint = Amber, modifier = Modifier.size(14.dp)); Spacer(Modifier.width(6.dp))
                                        Text(d, style = MaterialTheme.typography.labelMedium)
                                    }
                                }
                            }
                        }
                        g.link?.let { (url, label) ->
                            Row(Modifier.padding(top = 12.dp).clip(Corner).background(Electric.copy(alpha = 0.12f))
                                .clickable { ctx.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url))) }.padding(horizontal = 12.dp, vertical = 8.dp),
                                verticalAlignment = Alignment.CenterVertically) {
                                Text(label, color = Electric, style = MaterialTheme.typography.labelLarge); Spacer(Modifier.width(6.dp))
                                Icon(Icons.AutoMirrored.Outlined.OpenInNew, null, tint = Electric, modifier = Modifier.size(14.dp))
                            }
                        }
                        Spacer(Modifier.height(12.dp))
                        Text(if (isDone) "Mark as not done" else "Mark as done", color = if (isDone) Mute else Good, style = MaterialTheme.typography.labelLarge,
                            modifier = Modifier.clickable { done = if (isDone) done - g.title else done + g.title; saveDone(ctx, done) })
                    }
                }
            }
        }
    }
}
