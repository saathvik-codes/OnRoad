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
 * Twice a day: new manufacturer offers for the user's city and models newly listed on OnRoad (new launches show up here
 * as soon as the maker's site lists them). The first run only records what exists, so nothing old is announced.
 */
class AlertWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val deps = EntryPointAccessors.fromApplication(applicationContext, AlertDeps::class.java)
        val api = deps.api(); val prefs = deps.prefs()
        if (!prefs.alerts) return Result.success()
        val city = prefs.city.value
        return runCatching {
            val offers = api.offers(city)
            val seenO = prefs.seenOffers
            val newOffers = offers.filter { it.id.toString() !in seenO }
            if (seenO.isNotEmpty()) newOffers.take(3).forEach { o ->
                val who = listOfNotNull(o.brandName, o.modelName).joinToString(" ")
                notify(o.id.toInt(), if (o.amountInr != null) "$who: benefits up to ${lakhOrRupees(o.amountInr)}" else "New offer: $who",
                    o.title, "offers")
            }
            prefs.seenOffers = seenO + offers.map { it.id.toString() }

            val models = api.explore(city, type = "car") + api.explore(city, type = "bike")
            val seenM = prefs.seenModels
            if (seenM.isNotEmpty()) models.filter { it.id !in seenM }.take(3).forEach { m ->
                notify(m.id.hashCode(), "Now on OnRoad: ${m.brand} ${m.name}",
                    m.fromInr?.let { "Ex-showroom from ${lakhOrRupees(it)} in $city. See the full on-road price." } ?: "See variants and prices.", "model/${m.id}")
            }
            prefs.seenModels = seenM + models.map { it.id }
            Result.success()
        }.getOrElse { Result.retry() }
    }

    private fun lakhOrRupees(n: Long) = if (n >= 100_000) "₹%.2f L".format(n / 1e5).replace(".00", "") else "₹" + "%,d".format(n)

    private fun notify(id: Int, title: String, text: String, route: String) {
        val ctx = applicationContext
        if (Build.VERSION.SDK_INT >= 33 && ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) return
        val open = PendingIntent.getActivity(ctx, id, Intent(ctx, MainActivity::class.java).putExtra("route", route)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP), PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        NotificationManagerCompat.from(ctx).notify(id, NotificationCompat.Builder(ctx, CHANNEL).setSmallIcon(R.drawable.ic_stat_notify)
            .setColor(0xFFFF4D2E.toInt()).setContentTitle(title).setContentText(text).setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setContentIntent(open).setAutoCancel(true).build())
    }

    companion object {
        const val CHANNEL = "offers_launches"
        fun schedule(ctx: Context) {
            val nm = ctx.getSystemService(NotificationManager::class.java)
            nm.createNotificationChannel(NotificationChannel(CHANNEL, "Offers & new launches", NotificationManager.IMPORTANCE_DEFAULT)
                .apply { description = "Manufacturer offers in your city and newly listed cars and bikes" })
            WorkManager.getInstance(ctx).enqueueUniquePeriodicWork("alerts", ExistingPeriodicWorkPolicy.KEEP,
                PeriodicWorkRequestBuilder<AlertWorker>(12, TimeUnit.HOURS)
                    .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).build())
        }
    }
}
