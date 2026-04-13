import { useState } from "react";
import { PaymentElement, useStripe, useElements } from "@stripe/react-stripe-js";

export default function PaymentForm({ product, orderData }) {
  const stripe = useStripe();
  const elements = useElements();
  const [message, setMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!stripe || !elements) return;

    setIsProcessing(true);
    setMessage('⏳ Đang xử lý thanh toán và kiểm tra 3DS...');

    // Xác nhận thanh toán trực tiếp với Stripe
    const { paymentIntent, error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/`, 
      },
      redirect: "if_required",
    });

    // Xử lí kết quả
    if (error) {
      setIsProcessing(false);
      if (error.type === "card_error" || error.type === "validation_error") {
        setMessage(`❌ ${error.message}`);
      } else {
        setMessage("❌ Lỗi: " + error.message);
      }
    } 
    else if(paymentIntent && paymentIntent.status === 'succeeded'){
      setMessage("✅ Thanh toán thành công! Giao dịch đã được xác nhận.");
      setIsProcessing(false);
      // Có thể chuyển hướng hoặc update UI tại đây
      // window.location.href = '/success';
    }
  };

  return (
    <div style={styles.container}>
      <h2 style={styles.header}>Xác Nhận Thanh Toán</h2>
      
      <div style={styles.productBox}>
        <div>
          <span style={styles.label}>Sản phẩm</span>
          <span style={styles.value}>{product?.name || "Gói Dịch Vụ NT219"}</span>
        </div>
        <div>
          <span style={styles.label}>Tổng tiền</span>
          <span style={styles.price}>{product?.price || 0} VND</span>
        </div>
      </div>

      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.stripeBox}>
          <PaymentElement />
        </div>
        
        <button 
          disabled={isProcessing || !stripe || !elements} 
          style={{...styles.btn, opacity: (isProcessing || !stripe) ? 0.7 : 1}}
        >
          {isProcessing ? "Đang xử lý..." : "Thanh Toán Ngay"}
        </button>

        {message && (
          <div style={styles.messageBox}>
            {message}
          </div>
        )}
      </form>
    </div>
  );
}

const styles = {
  container: { background: 'linear-gradient(135deg, #0f0c29 0%, #24243e 100%)', padding: '35px', borderRadius: '24px', border: '1px solid rgba(255,255,255,0.1)', maxWidth: '450px', margin: '0 auto' },
  form: { width: '100%', color: '#fff', fontFamily: 'sans-serif' },
  header: { textAlign: 'center', marginBottom: '25px', color: '#fff' },
  productBox: { display: 'flex', justifyContent: 'space-between', background: 'rgba(255,255,255,0.05)', padding: '15px', borderRadius: '15px', marginBottom: '20px', color: '#fff' },
  label: { display: 'block', fontSize: '11px', color: '#aaa' },
  value: { fontWeight: 'bold', fontSize: '15px' },
  price: { fontWeight: 'bold', fontSize: '18px', color: '#00f2fe' },
  stripeBox: { background: 'white', padding: '15px', borderRadius: '12px', marginBottom: '20px' },
  btn: { width: '100%', padding: '16px', background: 'linear-gradient(to right, #667eea, #764ba2)', color: '#fff', border: 'none', borderRadius: '12px', fontWeight: 'bold', cursor: 'pointer', fontSize: '16px' },
  messageBox: { marginTop: '20px', padding: '15px', borderRadius: '10px', background: 'rgba(0,0,0,0.3)', color: '#fff', textAlign: 'center', fontSize: '14px' }
};