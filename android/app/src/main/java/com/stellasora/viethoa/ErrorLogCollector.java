package com.stellasora.viethoa;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.os.Build;
import android.widget.Toast;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class ErrorLogCollector {

    private static String lastError = "Chưa ghi nhận lỗi nghiêm trọng nào.";

    public static void recordError(String error) {
        lastError = error;
    }

    public static String generateReport(Context context) {
        String timestamp = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(new Date());

        StringBuilder sb = new StringBuilder();
        sb.append("### 📱 Báo Cáo Sự Cố Stella Sora (Android)\n");
        sb.append("- **Thời gian**: `").append(timestamp).append("`\n");
        sb.append("- **Thiết bị**: `").append(Build.MANUFACTURER).append(" ").append(Build.MODEL).append("`\n");
        sb.append("- **Thương hiệu**: `").append(Build.BRAND).append("`\n");
        sb.append("- **Android Version**: `").append(Build.VERSION.RELEASE)
          .append(" (SDK ").append(Build.VERSION.SDK_INT).append(")`\n");
        sb.append("- **Kiến trúc CPU**: `").append(Build.SUPPORTED_ABIS != null && Build.SUPPORTED_ABIS.length > 0 ? Build.SUPPORTED_ABIS[0] : "unknown").append("`\n");
        sb.append("- **Gói ứng dụng**: `com.YoStar.StellaSora`\n\n");

        sb.append("#### ⚠️ Lỗi Gần Nhất Ghi Nhận\n");
        sb.append("```text\n");
        sb.append(lastError).append("\n");
        sb.append("```\n\n");

        sb.append("---\n");
        sb.append("*Sao chép tự động từ ứng dụng Stella Sora Việt Hóa Android*\n");

        return sb.toString();
    }

    public static void copyToClipboard(Context context) {
        String report = generateReport(context);
        ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboard != null) {
            ClipData clip = ClipData.newPlainText("StellaSora_ErrorReport", report);
            clipboard.setPrimaryClip(clip);
            Toast.makeText(context, "✓ Đã sao chép mã lỗi vào bộ nhớ tạm! Hãy dán gửi cho Dev.", Toast.LENGTH_LONG).show();
        }
    }
}
