// グローバル変数
let currentImageIndex = 0;
let currentDate = '';
let allImages = [];
let imageToDelete = null;

// ページ読み込み完了時の処理
document.addEventListener('DOMContentLoaded', function() {
  // 日付フィルターのイベントリスナー設定
  document.getElementById('apply-filter').addEventListener('click', applyDateFilter);
  document.getElementById('reset-filter').addEventListener('click', resetDateFilter);
  
  // 画像モーダルのナビゲーションボタン設定
  document.getElementById('prev-btn').addEventListener('click', showPrevImage);
  document.getElementById('next-btn').addEventListener('click', showNextImage);
  
  // 削除確認ボタンの設定
  document.getElementById('confirm-delete').addEventListener('click', confirmDelete);
  document.getElementById('cancel-delete').addEventListener('click', cancelDelete);
  
  // キーボードイベントの設定
  document.addEventListener('keydown', handleKeyPress);
  
  // 削除された画像を非表示にする処理
  hideDeletedImages();
});

// 日付セクションの開閉
function toggleImages(date) {
  const imagesDiv = document.getElementById("images-" + date);
  imagesDiv.classList.toggle("hidden");
}

// 画像モーダルを開く
function openImageModal(imageSrc, index, date) {
  const modal = document.getElementById("image-modal");
  const modalImg = document.getElementById("modal-image");
  
  // 現在の日付の全画像を取得
  currentDate = date;
  collectImages(date);
  
  // インデックスをセット
  currentImageIndex = parseInt(index);
  
  // モーダルを表示
  modal.style.display = "block";
  modalImg.src = imageSrc;
  
  // スクロール無効化
  document.body.style.overflow = "hidden";
}

// 画像モーダルを閉じる
function closeImageModal() {
  const modal = document.getElementById("image-modal");
  modal.style.display = "none";
  
  // スクロール有効化
  document.body.style.overflow = "auto";
}

// 現在の日付の画像をすべて収集
function collectImages(date) {
  allImages = [];
  const imageContainer = document.getElementById("images-" + date);
  const imageItems = imageContainer.querySelectorAll(".image-item");
  
  imageItems.forEach(item => {
    const imgElement = item.querySelector("img");
    if (imgElement) {
      allImages.push(imgElement.src);
    }
  });
}

// 前の画像を表示
function showPrevImage() {
  if (allImages.length === 0) return;
  
  currentImageIndex--;
  if (currentImageIndex < 0) {
    currentImageIndex = allImages.length - 1;
  }
  
  document.getElementById("modal-image").src = allImages[currentImageIndex];
}

// 次の画像を表示
function showNextImage() {
  if (allImages.length === 0) return;
  
  currentImageIndex++;
  if (currentImageIndex >= allImages.length) {
    currentImageIndex = 0;
  }
  
  document.getElementById("modal-image").src = allImages[currentImageIndex];
}

// キーボード操作
function handleKeyPress(event) {
  const modal = document.getElementById("image-modal");
  
  // モーダルが表示されている場合のみキー操作を有効化
  if (modal.style.display === "block") {
    switch(event.key) {
      case "ArrowLeft":
        showPrevImage();
        break;
      case "ArrowRight":
        showNextImage();
        break;
      case "Escape":
        closeImageModal();
        break;
    }
  }
}

// 画像削除処理
function deleteImage(event, imagePath) { // 引数名は imagePath や relPath など、意味が通じればOK
  event.stopPropagation();
  imageToDelete = imagePath; // ここで 'history/your_image.png' 形式のパスが設定される
  document.getElementById("confirm-modal").style.display = "block";
}

/* 削除確認 */
function confirmDelete() {
  if (!imageToDelete) return;

  // imageToDelete は 'history/your_image.png' 形式のはず
  fetch('/api/delete_image', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ image_path: imageToDelete }) // この形式で送信
  })
  .then(res => res.json())
  .then(data => {
      if (data.success) {
        // data-image 属性が 'history/your_image.png' 形式で設定されていれば、
        // このセレクタは正しく動作します。
        document.querySelectorAll(`.image-item[data-image="${imageToDelete}"]`)
                .forEach(el => el.remove()); // または el.style.display = 'none';

        closeImageModal();
        showNotification('画像を削除しました', 'success');
      } else {
        showNotification(`削除失敗: ${data.message}`, 'error');
      }
      document.getElementById("confirm-modal").style.display = "none";
      imageToDelete = null;
  })
  .catch(err => {
      console.error(err);
      showNotification('通信エラー', 'error');
      document.getElementById("confirm-modal").style.display = "none";
  });
}

// 削除キャンセル
function cancelDelete() {
  imageToDelete = null;
  document.getElementById("confirm-modal").style.display = "none";
}

// 日付フィルタリングを適用
function applyDateFilter() {
  const fromDate = document.getElementById('date-from').value;
  const toDate = document.getElementById('date-to').value;
  
  // 日付が選択されていない場合は処理を中止
  if (!fromDate && !toDate) {
    alert('日付を選択してください');
    return;
  }
  
  // 全ての日付アイテムを取得
  const dateItems = document.querySelectorAll('.date-item');
  
  dateItems.forEach(item => {
    const itemDate = item.getAttribute('data-date');
    const formattedItemDate = `${itemDate.substring(0, 4)}-${itemDate.substring(4, 6)}-${itemDate.substring(6, 8)}`;
    
    let showItem = true;
    
    // 開始日が設定されている場合、その日付以降かどうかをチェック
    if (fromDate && formattedItemDate < fromDate) {
      showItem = false;
    }
    
    // 終了日が設定されている場合、その日付以前かどうかをチェック
    if (toDate && formattedItemDate > toDate) {
      showItem = false;
    }
    
    // 表示/非表示を切り替え
    if (showItem) {
      item.style.display = 'flex';
    } else {
      item.style.display = 'none';
      // 関連する画像コンテナも非表示
      const imagesDiv = document.getElementById(`images-${itemDate}`);
      if (imagesDiv) {
        imagesDiv.classList.add('hidden');
      }
    }
  });
}

// フィルターをリセット
function resetDateFilter() {
  // 日付入力をクリア
  document.getElementById('date-from').value = '';
  document.getElementById('date-to').value = '';
  
  // すべての日付アイテムを表示
  const dateItems = document.querySelectorAll('.date-item');
  dateItems.forEach(item => {
    item.style.display = 'flex';
  });
}

// 通知を表示する関数
function showNotification(message, type = 'info') {
  // 既存の通知を削除
  const existingNotification = document.getElementById('notification');
  if (existingNotification) {
    existingNotification.remove();
  }
  
  // 通知エレメントを作成
  const notification = document.createElement('div');
  notification.id = 'notification';
  notification.className = `notification ${type}`;
  notification.textContent = message;
  
  // bodyに追加
  document.body.appendChild(notification);
  
  // 数秒後に自動的に消す
  setTimeout(() => {
    notification.classList.add('notification-hide');
    setTimeout(() => {
      notification.remove();
    }, 500);
  }, 3000);
}

// 削除された画像をページロード時に非表示にする
function hideDeletedImages() {
  // サーバーから削除済み画像のリストを取得
  fetch('/api/get_deleted_images')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.deleted_images.length > 0) {
        // 削除済みの画像をページから非表示にする
        data.deleted_images.forEach(imagePath => {
          const imageElements = document.querySelectorAll(`.image-item[data-image="${imagePath}"]`);
          imageElements.forEach(el => {
            el.style.display = 'none';
          });
        });
      }
    })
    .catch(error => {
      console.error('削除済み画像の取得に失敗しました:', error);
    });
}