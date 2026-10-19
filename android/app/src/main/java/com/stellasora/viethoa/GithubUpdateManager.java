package com.stellasora.viethoa;

import android.os.Handler;
import android.os.Looper;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class GithubUpdateManager {

    public interface Callback {
        void onSuccess(String result);
        void onError(String error);
    }

    private static final String NOTIFS_URL =
            "https://raw.githubusercontent.com/doubleD1302/AmeeVH/main/launcher/notifications.json";

    public static void fetchAnnouncements(final Callback callback) {
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    URL url = new URL(NOTIFS_URL);
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                    conn.setConnectTimeout(5000);
                    conn.setReadTimeout(5000);
                    conn.setRequestProperty("User-Agent", "StellaSora-Android");

                    if (conn.getResponseCode() == 200) {
                        BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()));
                        StringBuilder sb = new StringBuilder();
                        String line;
                        while ((line = reader.readLine()) != null) {
                            sb.append(line).append("\n");
                        }
                        reader.close();

                        JSONObject json = new JSONObject(sb.toString());
                        JSONArray announcements = json.optJSONArray("announcements");

                        final StringBuilder formatted = new StringBuilder();
                        if (announcements != null) {
                            for (int i = 0; i < announcements.length(); i++) {
                                JSONObject item = announcements.getJSONObject(i);
                                formatted.append("📌 [").append(item.optString("date", "")).append("] ")
                                         .append(item.optString("title", "")).append("\n")
                                         .append(item.optString("content", "")).append("\n\n");
                            }
                        }

                        new Handler(Looper.getMainLooper()).post(new Runnable() {
                            @Override
                            public void run() {
                                callback.onSuccess(formatted.toString());
                            }
                        });
                    } else {
                        throw new Exception("HTTP response code: " + conn.getResponseCode());
                    }
                } catch (final Exception e) {
                    new Handler(Looper.getMainLooper()).post(new Runnable() {
                        @Override
                        public void run() {
                            callback.onError("Không thể tải thông báo online: " + e.getMessage() +
                                    "\n(Đang dùng thông báo ngoại tuyến mặc định)");
                        }
                    });
                }
            }
        }).start();
    }
}
