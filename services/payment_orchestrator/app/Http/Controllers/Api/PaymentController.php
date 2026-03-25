<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Stripe\Stripe;
use Stripe\PaymentIntent;
use Illuminate\Support\Facades\Http;

class PaymentController extends Controller
{
    public function charge(Request $request)
    {
        Stripe::setApiKey(env('STRIPE_SECRET'));

        // Lúc này Frontend nó chỉ gửi 2 món này sang thôi
        $amount = $request->input('amount', 50000); 
        $orderId = $request->input('order_id');

        // Query số lần thất bại, giờ mock tạm là 0 hoặc 1 để test
        $failedAttempts = $request->input('failed_attempts', 0);

        try {
            // Gọi Fraud Engine xin điểm rủi ro
            $fraudRes = Http::timeout(5)->post('http://host.docker.internal:8001/api/fraud/score',[
                'amount' => $amount,
                'failed_attempts' => $failedAttempts
            ]);

            // Nếu Python lỗi và không trả data
            if (!$fraudRes->successful()) {
            return response()->json([
                'error' => 'AI bị lỗi ',
                'detail' => $fraudRes->json() // In lỗi
            ], 500);
            }

            $fraudData = $fraudRes->json();

            // Xử lí theo quyết định AI
            if($fraudData['action'] === 'block'){
                return response()->json([
                    'error' => "Giao dịch bị từ chối do rủi ro gian lận cao",
                    'fraud_score' => $fraudData['score'],
                    'reason' => $fraudData['reason']
                ], 403);
            }

            // Nếu AI khả nghi thì bật force3ds true
            $force3ds = ($fraudData['action'] === 'force_3ds');

            // Chuyển tiếp cho Stripe(PSP)
            Stripe::setApiKey(env('STRIPE_SECRET'));
            $paymentIntent = PaymentIntent::create([
                'amount' => $amount,
                'currency' => 'vnd',
                'metadata' => [
                    'order_id' => $orderId,
                    'fraud_score' => $fraudData['score']
                ],
                'payment_method_options' => [
                    'card' => [
                        // Kích hoạt 3DS phụ thuộc theo lệnh AI
                        'request_three_d_secure' => $force3ds ? 'any' : 'automatic',
                    ],
                ],
            ]);

            return response()->json([
                'client_secret' => $paymentIntent->client_secret,
                'fraud_score' => $fraudData['score'],
                'action' => $fraudData['action']
            ]);

        } catch (\Exception $e) {
            return response()->json(['error' => $e->getMessage()], 500);
        }
    }
}
