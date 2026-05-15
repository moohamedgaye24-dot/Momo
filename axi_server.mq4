//+------------------------------------------------------------------+
//|                                                   axi_server.mq4 |
//|                                      Autonomous Institutional EA |
//|                                          ZeroMQ Python/MT4 Bridge|
//+------------------------------------------------------------------+
#property copyright "Autonomous System"
#property link      "https://github.com/"
#property version   "1.00"
#property strict

//--- ZeroMQ Includes
#include <Zmq/Zmq.mqh>

extern string BindAddress = "tcp://*:5555";
extern int    MagicNumber = 12345;
extern int    Slippage    = 30;

Context zmq_context;
Socket  zmq_socket;

int OnInit() {
   if(!zmq_context.Init() || !zmq_socket.Init(zmq_context, ZMQ_REP) || !zmq_socket.Bind(BindAddress)) return(INIT_FAILED);
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) { zmq_socket.Close(); zmq_context.Destroy(); }

void OnTick() {
   ZmqMsg request;
   if(zmq_socket.Recv(request, ZMQ_DONTWAIT)) {
      string json_str = request.String();
      string action = ParseJSONValue(json_str, "action");
      string symbol = ParseJSONValue(json_str, "symbol");
      string type   = ParseJSONValue(json_str, "type");
      double lots   = StringToDouble(ParseJSONValue(json_str, "lots"));
      double sl     = StringToDouble(ParseJSONValue(json_str, "sl"));
      double tp     = StringToDouble(ParseJSONValue(json_str, "tp"));

      string response_msg = "UNKNOWN_COMMAND";
      if(action == "TRADE" || action == "OPEN") response_msg = ExecuteTrade(symbol, type, lots, sl, tp);
      else if (action == "CLOSE") response_msg = CloseAllTrades(symbol);

      ZmqMsg reply(response_msg);
      zmq_socket.Send(reply);
   }
}

string ExecuteTrade(string sym, string type, double lots, double sl, double tp) {
   int cmd = -1;
   if(type == "OP_BUY") cmd = OP_BUY;
   else if(type == "OP_SELL") cmd = OP_SELL;
   if(cmd == -1) return "INVALID_ORDER_TYPE";
   double point = MarketInfo(sym, MODE_POINT);
   double digits = MarketInfo(sym, MODE_DIGITS);
   double pips_multiplier = (digits == 3 || digits == 5) ? 10.0 : 1.0;
   RefreshRates();
   double price = (cmd == OP_BUY) ? MarketInfo(sym, MODE_ASK) : MarketInfo(sym, MODE_BID);
   int ticket = OrderSend(sym, cmd, lots, price, Slippage * (int)pips_multiplier, sl, tp, "ZMQ Bridge", MagicNumber, 0, clrNONE);
   if(ticket > 0) return "ORDER_SUCCESS_" + IntegerToString(ticket);
   else return "ORDER_FAILED_ERR_" + IntegerToString(GetLastError());
}

string CloseAllTrades(string sym) {
   int closed_count = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--) {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES) && OrderSymbol() == sym && OrderMagicNumber() == MagicNumber) {
         double price = (OrderType() == OP_BUY) ? MarketInfo(sym, MODE_BID) : MarketInfo(sym, MODE_ASK);
         if(OrderClose(OrderTicket(), OrderLots(), price, Slippage, clrNONE)) closed_count++;
      }
   }
   return "CLOSED_" + IntegerToString(closed_count) + "_TRADES";
}

string ParseJSONValue(string json, string key) {
   string search_key = "\"" + key + "\":";
   int start_idx = StringFind(json, search_key);
   if(start_idx == -1) return "";
   start_idx += StringLen(search_key);
   int val_start = start_idx;
   bool is_string = false;
   while(StringSubstr(json, val_start, 1) == " " || StringSubstr(json, val_start, 1) == "\"") {
      if(StringSubstr(json, val_start, 1) == "\"") is_string = true;
      val_start++;
   }
   int val_end = val_start;
   while(val_end < StringLen(json)) {
      string c = StringSubstr(json, val_end, 1);
      if((is_string && c == "\"") || (!is_string && (c == "," || c == "}"))) break;
      val_end++;
   }
   return StringSubstr(json, val_start, val_end - val_start);
}
