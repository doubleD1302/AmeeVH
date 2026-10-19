package com.stellasora.viethoa;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {

    private static final int OVERLAY_PERMISSION_REQ_CODE = 1234;
    private TextView tvStatus;
    private TextView tvAnnouncements;
    private boolean isOverlayRunning = false;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        tvStatus = findViewById(R.id.tvStatus);
        tvAnnouncements = findViewById(R.id.tvAnnouncements);
        Button btnToggleOverlay = findViewById(R.id.btnToggleOverlay);
        Button btnCheckUpdate = findViewById(R.id.btnCheckUpdate);
        Button btnCopyError = findViewById(R.id.btnCopyError);

        tvStatus.setText("✓ Đã sẵn sàng kết nối Local ADB và cập nhật");

        btnToggleOverlay.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                toggleFloatingOverlay();
            }
        });

        btnCheckUpdate.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                checkGithubUpdate();
            }
        });

        btnCopyError.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                ErrorLogCollector.copyToClipboard(MainActivity.this);
            }
        });

        loadAnnouncements();
    }

    private void toggleFloatingOverlay() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
            Intent intent = new Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:" + getPackageName()));
            startActivityForResult(intent, OVERLAY_PERMISSION_REQ_CODE);
            Toast.makeText(this, "Vui lòng cấp quyền 'Hiển thị trên các ứng dụng khác'", Toast.LENGTH_LONG).show();
            return;
        }

        Intent serviceIntent = new Intent(this, FloatingOverlayService.class);
        if (!isOverlayRunning) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                startForegroundService(serviceIntent);
            } else {
                startService(serviceIntent);
            }
            isOverlayRunning = true;
            Toast.makeText(this, "Đã bật thông báo nổi!", Toast.LENGTH_SHORT).show();
        } else {
            stopService(serviceIntent);
            isOverlayRunning = false;
            Toast.makeText(this, "Đã tắt thông báo nổi!", Toast.LENGTH_SHORT).show();
        }
    }

    private void checkGithubUpdate() {
        Toast.makeText(this, "Đang kết nối GitHub kiểm tra phiên bản mới...", Toast.LENGTH_SHORT).show();
        GithubUpdateManager.fetchAnnouncements(new GithubUpdateManager.Callback() {
            @Override
            public void onSuccess(String result) {
                tvAnnouncements.setText(result);
                Toast.makeText(MainActivity.this, "Đã cập nhật thông báo mới từ GitHub!", Toast.LENGTH_SHORT).show();
            }

            @Override
            public void onError(String error) {
                Toast.makeText(MainActivity.this, error, Toast.LENGTH_LONG).show();
            }
        });
    }

    private void loadAnnouncements() {
        GithubUpdateManager.fetchAnnouncements(new GithubUpdateManager.Callback() {
            @Override
            public void onSuccess(String result) {
                tvAnnouncements.setText(result);
            }

            @Override
            public void onError(String error) {
                tvAnnouncements.setText("📢 Thông Báo Offline:\n\n" +
                        "1. Dự án Việt hóa Stella Sora đã hỗ trợ APK & Local ADB.\n" +
                        "2. Nhấn nút 'Bật Thông Báo Nổi' để hiển thị widget trạng thái nổi trên game.\n" +
                        "3. Bấm 'Sao chép mã lỗi cho Dev' khi cần hỗ trợ kỹ thuật.");
            }
        });
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == OVERLAY_PERMISSION_REQ_CODE) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && Settings.canDrawOverlays(this)) {
                toggleFloatingOverlay();
            }
        }
    }
}
