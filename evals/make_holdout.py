"""Held-out set: written after the rules were frozen, never used to tune them.
Messier phrasing, typos, negations and other EMEA languages."""
import json
from make_cases import c, R, H
cases = [
 c("H01","hey so i got this voucher on friday for a massage and honestly dont need it anymore, can u reverse it","cancel_refund",R,"P-LOCAL-CANCEL",days_since_purchase=4),
 c("H02","Hola, compré un bono de spa hace dos días y quiero que me devolváis el dinero.","cancel_refund",R,"P-LOCAL-CANCEL",days_since_purchase=2),
 c("H03","Buongiorno, il ristorante ha chiuso definitivamente. Come posso avere il rimborso?","merchant_closed",R,"P-MERCHANT-CLOSED",days_since_purchase=30),
 c("H04","the place wouldn't let me in with the coupon, guy at the desk said its not a valid code and it's NOT expired","merchant_refused",H,"P-MERCHANT-REFUSED"),
 c("H05","Is there any way to push my booking for the boat trip to a later date?","appointment_change",R,"P-APPT-CHANGE",appointment_booked=True),
 c("H06","Mi bono aparece como canjeado pero yo no lo he usado nunca.","already_redeemed",H,"P-ALREADY-REDEEMED",redeemed=True),
 c("H07","got charged twice for the same deal??","other",H,"ESC-LOWCONF"),
 c("H08","My mum has been very ill and in and out of hospital, she couldn't use her voucher before it ran out.","expired_voucher",H,"P-EXPIRED",expired=True,days_since_purchase=150),
 c("H09","the blender came with a cracked jug","goods_faulty",R,"P-GOODS-RETURN",deal_type="goods",days_since_delivery=3),
 c("H10","Ho cancellato l'ordine lunedì, quando arriva il rimborso sulla carta?","refund_status",R,"P-REFUND-TIMING"),
 c("H11","I'm talking to my solicitor about this deal if it isn't sorted","complaint",H,"ESC-LEGAL",redeemed=True),
 c("H12","Can't get through to the merchant at all, tried phone email and instagram","merchant_closed",R,"P-MERCHANT-CLOSED",days_since_purchase=25),
 c("H13","no slots left for any date before my voucher ends, what now","cant_book",R,"P-CANT-BOOK",days_since_purchase=60),
 c("H14","I'd rather have the cash than bucks for the cancelled gig please","live_event",R,"P-LIVE",deal_type="live",event_cancelled=True,final_sale=True),
 c("H15","Someone used my account to buy 3 vouchers this morning","fraud",H,"ESC-FRAUD"),
 c("H16","No encuentro el código del bono en la app","find_voucher",R,"P-FIND-VOUCHER"),
 c("H17","I didn't realise the voucher had a time limit, it lapsed last week","expired_voucher",R,"P-EXPIRED",expired=True,days_since_purchase=180),
 c("H18","fourth time asking. refund for the facial. sort it out.","refund_status",H,"ESC-REPEAT",prior_contacts=3),
 c("H19","Want to send back the jacket, wrong size, came on tuesday","goods_return",R,"P-GOODS-RETURN",deal_type="goods",days_since_delivery=2),
 c("H20","Quiero cancelar la reserva del hotel, el establecimiento no contesta y ya pagué.","merchant_closed",R,"P-MERCHANT-CLOSED",deal_type="getaway",days_since_purchase=15),
]
if __name__ == "__main__":
    json.dump(cases, open(__import__("os").path.join(__import__("os").path.dirname(__file__),"holdout.json"),"w"), indent=1, ensure_ascii=False)
    print(len(cases), "holdout cases")
