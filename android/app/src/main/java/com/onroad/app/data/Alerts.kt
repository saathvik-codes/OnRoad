package com.onroad.app.data

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.onroad.app.MainActivity
import com.onroad.app.R
import dagger.hilt.EntryPoint
import dagger.hilt.InstallIn
import dagger.hilt.android.EntryPointAccessors
import dagger.hilt.components.SingletonComponent
import java.util.concurrent.TimeUnit

@EntryPoint
@InstallIn(SingletonComponent::class)
interface AlertDeps { fun api(): Api; fun prefs(): Prefs }

/**
 * Every 6 hours: new manufacturer offers for the user's city and models newly listed on OnRoad (new launches show up here
 * as soon as the maker's site lists them). The first run only records what exists, so nothing old is announced.
 */
class AlertWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val deps = EntryPointAccessors.fromApplication(applicationContext, AlertDeps::class.java)
        val api = deps.api(); val prefs = deps.prefs()
        if (!prefs.alerts) return Result.success()
        val city = prefs.city.value
        // quiet hours: nothing between 10 pm and 8 am; the news waits for the next run (seen-sets aren't updated)
        val hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY)
        if (hour >= 22 || hour < 8) return Result.success()
        return runCatching {
            val offers = api.offers(city)
            fun key(o: OfferItem) = listOf(o.brandSlug, o.modelName.orEmpty(), o.title, o.amountInr?.toString().orEmpty()).joinToString("|").lowercase()
            val seenO = prefs.seenOffers
            val newOffers = offers.filter { key(it) !in seenO }.distinctBy { key(it) }
            if (seenO.isNotEmpty()) newOffers.take(3).forEach { o ->
                val who = listOfNotNull(o.brandName, o.modelName).joinToString(" ")
                val title = if (o.amountInr != null) "🎁 ${lakhOrRupees(o.amountInr)} off the $who in $city" else "🎁 Fresh deal on the $who"
                val text = o.title + (o.validUntil?.let { " Ends $it, don't sleep on it." } ?: "")
                notify(key(o).hashCode(), title, text, "offers", prefs.img(o.modelImage, 720), "See the offer")
            }
            prefs.seenOffers = seenO + offers.map(::key)

            val models = api.explore(city, type = "car") + api.explore(city, type = "bike")
            val seenM = prefs.seenModels
            if (seenM.isNotEmpty()) models.filter { it.id !in seenM }.take(3).forEach { m ->
                notify(m.id.hashCode(), "🚗 Just landed: ${m.brand} ${m.name}",
                    m.fromInr?.let { "Starts at ${lakhOrRupees(it)} ex-showroom in $city. Tap for the real on-road price, taxes and all." }
                        ?: "Variants and prices are up. Take a look.", "model/${m.id}", prefs.img(m.imageUrl, 720), "See on-road price")
            }
            prefs.seenModels = seenM + models.map { it.id }
            Result.success()
        }.getOrElse { Result.retry() }
    }

    private fun lakhOrRupees(n: Long) = if (n >= 100_000) "₹%.2f L".format(n / 1e5).replace(".00", "") else "₹" + "%,d".format(n)

    private fun notify(id: Int, title: String, text: String, route: String, image: String? = null, action: String? = null) {
        val ctx = applicationContext
        if (Build.VERSION.SDK_INT >= 33 && ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return
        val open = PendingIntent.getActivity(ctx, id, Intent(ctx, MainActivity::class.java).putExtra("route", route)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val pic = loadBitmap(image)                 // the car's picture, shown when the notification is expanded
        NotificationManagerCompat.from(ctx).notify(id, NotificationCompat.Builder(ctx, CHANNEL).setSmallIcon(R.drawable.ic_stat_notify)
            .setColor(0xFFFF4D2E.toInt()).setContentTitle(title).setContentText(text)
            .setStyle(if (pic != null) NotificationCompat.BigPictureStyle().bigPicture(pic).setSummaryText(text) else NotificationCompat.BigTextStyle().bigText(text))
            .setLargeIcon(pic).setContentIntent(open).setAutoCancel(true)
            .apply { if (action != null) addAction(0, action, open) }.build())
    }

    companion object {
        const val CHANNEL = "offers_launches"
        fun schedule(ctx: Context) {
            val nm = ctx.getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(NotificationChannel(CHANNEL, "Offers & new launches", NotificationManager.IMPORTANCE_DEFAULT)
                .apply { description = "Manufacturer offers in your city and newly listed cars and bikes" })
            WorkManager.getInstance(ctx).enqueueUniquePeriodicWork("alerts", ExistingPeriodicWorkPolicy.KEEP,
                PeriodicWorkRequestBuilder<AlertWorker>(6, TimeUnit.HOURS)
                    .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).build())
        }
    }
}


/** Small, time-boxed image download for notification pictures; null on any problem (the text still shows). */
fun loadBitmap(url: String?): android.graphics.Bitmap? = url?.let {
    runCatching {
        val c = java.net.URL(it).openConnection() as java.net.HttpURLConnection
        c.connectTimeout = 5000; c.readTimeout = 8000
        c.inputStream.use { s -> android.graphics.BitmapFactory.decodeStream(s) }.also { c.disconnect() }
    }.getOrNull()
}
