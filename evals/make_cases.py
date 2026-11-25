"""Generates evals/cases.json. Tickets are synthetic: written from common public
complaint themes, not copied from any review. Order records are invented."""
import json

D = dict(deal_type="local", days_since_purchase=5, redeemed=False, appointment_booked=False,
         expired=False, final_sale=False, payment_valid=True, event_cancelled=False,
         days_since_delivery=None, prior_contacts=0)

def c(id, text, intent, action, policy, **order):
    return {"id": id, "text": text, "order": {**D, **order},
            "expected": {"intent": intent, "action": action, "policy": policy}}

R, H = "resolve", "handoff"
cases = [
 # --- cancel / refund: local ---
 c("T01","Hi, I bought a spa day voucher 3 days ago and changed my mind. Can I get my money back?","cancel_refund",R,"P-LOCAL-CANCEL",days_since_purchase=3),
 c("T02","I'd like to cancel the cooking class I purchased last week, haven't used it yet.","cancel_refund",R,"P-LOCAL-CANCEL",days_since_purchase=7),
 c("T03","Can I get a refund for the massage voucher? I bought it about a month ago, never used it.","cancel_refund",R,"P-LOCAL-CANCEL",days_since_purchase=31),
 c("T04","I want to cancel my order but I already booked an appointment for Saturday.","cancel_refund",R,"P-LOCAL-CANCEL",days_since_purchase=4,appointment_booked=True),
 c("T05","Please refund my voucher, bought yesterday. The card I paid with was cancelled after my wallet got stolen.","cancel_refund",H,"P-PAYMENT-CHANGED",days_since_purchase=1,payment_valid=False),
 c("T06","I don't want Groupon credits, I want my money back on my card for the yoga pass.","cancel_refund",R,"P-LOCAL-CANCEL",days_since_purchase=6),
 # --- expired ---
 c("T07","My voucher for the escape room expired last month, can I still use it or get a refund?","expired_voucher",R,"P-EXPIRED",days_since_purchase=200,expired=True),
 c("T08","Voucher expired while I was in hospital for 6 weeks. I couldn't use it. Please help.","expired_voucher",H,"P-EXPIRED",days_since_purchase=120,expired=True),
 c("T09","The restaurant voucher expired yesterday, I forgot about it. Any chance?","expired_voucher",R,"P-EXPIRED",days_since_purchase=90,expired=True),
 # --- already redeemed ---
 c("T10","My voucher says redeemed but I never used it! Someone else must have.","already_redeemed",H,"P-ALREADY-REDEEMED",redeemed=True),
 c("T11","App shows my teeth whitening voucher as used. I haven't been there yet.","already_redeemed",H,"P-ALREADY-REDEEMED",redeemed=True),
 # --- merchant refused ---
 c("T12","The salon refused to accept my voucher today, said they don't take Groupon anymore.","merchant_refused",H,"P-MERCHANT-REFUSED"),
 c("T13","Merchant won't accept the code, says it's not valid. It's not expired.","merchant_refused",H,"P-MERCHANT-REFUSED"),
 # --- merchant closed / unreachable ---
 c("T14","The gym has closed down permanently. What happens to my voucher?","merchant_closed",R,"P-MERCHANT-CLOSED",days_since_purchase=40),
 c("T15","I've been calling the hotel for two weeks, nobody answers the phone or emails.","merchant_closed",R,"P-MERCHANT-CLOSED",deal_type="getaway",days_since_purchase=20),
 # --- booking ---
 c("T16","I can't find any available dates to book my paintball session.","cant_book",R,"P-CANT-BOOK",days_since_purchase=10),
 c("T17","How do I move my facial appointment from Thursday to next week?","appointment_change",R,"P-APPT-CHANGE",appointment_booked=True),
 c("T18","I need to cancel tomorrow's appointment, something came up.","appointment_change",R,"P-APPT-CHANGE",appointment_booked=True),
 c("T19","Can I book the second session of my laser package before the first one?","appointment_change",R,"P-APPT-CHANGE",appointment_booked=True),
 # --- goods ---
 c("T20","The headphones I ordered arrived yesterday, I want to send them back.","goods_return",R,"P-GOODS-RETURN",deal_type="goods",days_since_delivery=1),
 c("T21","Want to return the air fryer, it arrived 3 weeks ago, I just don't like it.","goods_return",R,"P-GOODS-RETURN",deal_type="goods",days_since_delivery=21),
 c("T22","The vacuum stopped working after 2 days. It's broken. What do I do?","goods_faulty",R,"P-GOODS-RETURN",deal_type="goods",days_since_delivery=2),
 c("T23","I sent the watch back to the seller a month ago and still no refund. This is my third message about it.","refund_status",H,"P-GOODS-RETURN",deal_type="goods",days_since_delivery=45,prior_contacts=2),
 # --- refund status ---
 c("T24","You confirmed my refund 3 days ago, it's not on my card yet. When will it arrive?","refund_status",R,"P-REFUND-TIMING"),
 c("T25","Where is my refund?? Cancelled on Monday.","refund_status",R,"P-REFUND-TIMING"),
 # --- live ---
 c("T26","The concert was cancelled by the organiser. How do I get my money back?","live_event",R,"P-LIVE",deal_type="live",event_cancelled=True,final_sale=True),
 c("T27","Bought theatre tickets an hour ago by mistake, wrong date. Can I cancel?","live_event",R,"P-LIVE",deal_type="live",days_since_purchase=0),
 c("T28","I can't go to the show anymore, can I get a refund? Bought them last week.","live_event",R,"P-LIVE",deal_type="live",days_since_purchase=7,final_sale=True),
 # --- safety handoffs ---
 c("T29","If I don't get a refund today I'm filing a chargeback with my bank.","cancel_refund",H,"ESC-LEGAL",days_since_purchase=20),
 c("T30","I will report you to trading standards, the spa was nothing like the description.","complaint",H,"ESC-LEGAL",redeemed=True),
 c("T31","There's a purchase on my account I didn't make. I think I've been hacked.","fraud",H,"ESC-FRAUD"),
 c("T32","My husband passed away and he had bought us a weekend away. I can't go. Can I get the money back?","cancel_refund",H,"ESC-VULNERABLE",deal_type="getaway",days_since_purchase=60),
 c("T33","Still waiting on my refund for the massage, this is the third time I write. Nobody fixes it.","refund_status",H,"ESC-REPEAT",prior_contacts=2),
 # --- ambiguous / multi-intent ---
 c("T34","hello","other",H,"ESC-LOWCONF"),
 c("T35","My voucher expired and also the merchant closed before I could use it, and I want a refund.","merchant_closed",H,"ESC-LOWCONF",expired=True,days_since_purchase=150),
 c("T36","Where can I find my voucher code? I can't see it in the app.","find_voucher",R,"P-FIND-VOUCHER"),
]
if __name__ == "__main__":
    json.dump(cases, open(__import__("os").path.join(__import__("os").path.dirname(__file__),"cases.json"),"w"), indent=1, ensure_ascii=False)
    print(len(cases), "cases")
