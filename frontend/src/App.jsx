import { useEffect, useState } from 'react';
import Checkout from './components/Checkout';
import ProductList from './components/ProductList';
import Login from './components/Login';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Lưu phiên thanh toán khi API trả về client_secret
  const [checkoutSession, setCheckoutSession] = useState(null);

  // Kiểm tra xem user đã có thẻ thông hành (JWT) chưa khi vừa vào trang
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  // Xử lý khi user bấm nút Mua Sản Phẩm
  const handleBuyClick = async (product) => {
    setSelectedProduct(product);
    setErrorMsg('');
    setIsProcessing(true);

    const token = localStorage.getItem('access_token');
    if (!token) {
      alert("Phiên đăng nhập hết hạn, vui lòng đăng nhập lại!");
      setIsAuthenticated(false);
      return;
    }

    try {
      // GỌI THẲNG XUỐNG BACKEND, KHÔNG CẦN HỎI EMAIL NỮA
      const response = await fetch('http://localhost:5050/api/orders/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          product_id: product.id,
          quantity: 1
        }),
      });

      const data = await response.json();
      
      if (response.ok && data.status === 'success') {
        setCheckoutSession({
          clientSecret: data.client_secret,
          orderData: data
        });
      } else {
        setErrorMsg(data.error || data.detail || 'Lỗi giao dịch!');
        if (response.status === 401) {
          localStorage.removeItem('access_token');
          setIsAuthenticated(false);
        }
      }

    } catch (err) {
      setErrorMsg('Lỗi kết nối đến Server API!');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleBackToStore = () => {
    setCheckoutSession(null);
    setSelectedProduct(null);
    setErrorMsg('');
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <Login onLoginSuccess={() => setIsAuthenticated(true)} />;
  }
  return (
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column',
      minHeight: '100vh', backgroundColor: '#1a1a1a', fontFamily: 'Arial, sans-serif',
      color: 'white', position: 'relative'
    }}>

      <div style={{ position: 'absolute', top: '20px', right: '20px' }}>
        <button onClick={handleLogout} style={styles.logoutBtn}>
          Đăng xuất
        </button>
      </div>

      {checkoutSession && (
        <button onClick={handleBackToStore} style={styles.backBtn}>
          ← Quay lại cửa hàng
        </button>
      )}

      {errorMsg && <div style={styles.errorMsg}>❌ {errorMsg}</div>}
      
      {isProcessing && <div style={{color: '#00f2fe', marginBottom: '15px'}}>Đang khởi tạo giao dịch bảo mật...</div>}
      {!checkoutSession ? (
        <ProductList onSelectProduct={handleBuyClick} />
      ) : (
        <Checkout product={selectedProduct} session={checkoutSession} />
      )}

    </div>
  );
}

const styles = {
  backBtn: { position: 'absolute', top: '20px', left: '20px', padding: '8px 16px', backgroundColor: 'transparent', border: '1px solid #fff', color: '#fff', borderRadius: '4px', cursor: 'pointer' },
  logoutBtn: { padding: '8px 16px', backgroundColor: '#ff4757', border: 'none', color: '#000000', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' },
  errorMsg: { marginBottom: '15px', padding: '10px', background: 'rgba(255,0,0,0.1)', color: '#ff4757', borderRadius: '8px', fontSize: '14px', border: '1px solid #ff4757' }
};

export default App;