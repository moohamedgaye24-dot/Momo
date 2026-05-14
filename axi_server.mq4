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

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   Print("Initializing ZeroMQ MT4 Bridge Server...");

   if(!zmq_context.Init()) {
      Print("Failed to initialize ZMQ Context.");
      return(INIT_FAILED);
   }

   if(!zmq_socket.Init(zmq_context, ZMQ_REP)) {
      Print("Failed to initialize ZMQ Socket.");
      return(INIT_FAILED);
   }

   if(!zmq_socket.Bind(BindAddress)) {
      Print("Failed to bind ZMQ Socket to ", BindAddress);
      return(INIT_FAILED);
   }

   Print("MT4 ZMQ Bridge successfully bound to ", BindAddress);
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   Print("Deinitializing ZMQ MT4 Bridge...");
   zmq_socket.Close();
   zmq_context.Destroy();
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   // Check for incoming messages without blocking
   ZmqMsg request;
   if(zmq_socket.Recv(request, ZMQ_DONTWAIT)) {
      string json_str = request.String();
      Print("Received Payload: ", json_str);

      // Basic string parsing to handle JSON since native MQL4 lacks a built-in JSON parser
      string action = ParseJSONValue(json_str, "action");
      string symbol = ParseJSONValue(json_str, "symbol");
      string type   = ParseJSONValue(json_str, "type");
      double lots   = StringToDouble(ParseJSONValue(json_str, "lots"));
      double sl     = StringToDouble(ParseJSONValue(json_str, "sl"));
      double tp     = StringToDouble(ParseJSONValue(json_str, "tp"));

      string response_msg = "UNKNOWN_COMMAND";

      if(action == "TRADE" || action == "OPEN") {
         response_msg = ExecuteTrade(symbol, type, lots, sl, tp);
      }
      else if (action == "CLOSE") {
         response_msg = CloseAllTrades(symbol);
      }
      else if (action == "MODIFY") {
         response_msg = "MODIFY_COMMAND_RECEIVED_NOT_IMPLEMENTED_IN_MOCK";
      }

      // Send Reply back to Python
      ZmqMsg reply(response_msg);
      zmq_socket.Send(reply);
   }
  }

//+------------------------------------------------------------------+
//| Trade Execution Engine                                           |
//+------------------------------------------------------------------+
string ExecuteTrade(string sym, string type, double lots, double sl, double tp)
  {
   int cmd = -1;
   if(type == "OP_BUY") cmd = OP_BUY;
   else if(type == "OP_SELL") cmd = OP_SELL;

   if(cmd == -1) return "INVALID_ORDER_TYPE";

   // Handle 5-digit pricing and Gold (XAUUSD) specific points
   double point = MarketInfo(sym, MODE_POINT);
   double digits = MarketInfo(sym, MODE_DIGITS);
   double pips_multiplier = 1.0;

   if(digits == 3 || digits == 5) pips_multiplier = 10.0;

   // Refresh rates before execution
   RefreshRates();
   double price = (cmd == OP_BUY) ? MarketInfo(sym, MODE_ASK) : MarketInfo(sym, MODE_BID);

   int ticket = OrderSend(sym, cmd, lots, price, Slippage * (int)pips_multiplier, sl, tp, "ZMQ Bridge", MagicNumber, 0, clrNONE);

   if(ticket > 0) {
      return "ORDER_SUCCESS_" + IntegerToString(ticket);
   } else {
      int err = GetLastError();
      return "ORDER_FAILED_ERR_" + IntegerToString(err);
   }
  }

//+------------------------------------------------------------------+
//| Close Trades Engine                                              |
//+------------------------------------------------------------------+
string CloseAllTrades(string sym)
  {
   int closed_count = 0;
   for(int i = OrdersTotal() - 1; i >= 0; i--) {
      if(OrderSelect(i, SELECT_BY_POS, MODE_TRADES)) {
         if(OrderSymbol() == sym && OrderMagicNumber() == MagicNumber) {
            double price = (OrderType() == OP_BUY) ? MarketInfo(sym, MODE_BID) : MarketInfo(sym, MODE_ASK);
            if(OrderClose(OrderTicket(), OrderLots(), price, Slippage, clrNONE)) {
               closed_count++;
            }
         }
      }
   }
   return "CLOSED_" + IntegerToString(closed_count) + "_TRADES";
  }

//+------------------------------------------------------------------+
//| Utility: Simple JSON Parser (Mock)                               |
//+------------------------------------------------------------------+
string ParseJSONValue(string json, string key)
  {
   string search_key = "\"" + key + "\":";
   int start_idx = StringFind(json, search_key);
   if(start_idx == -1) return "";

   start_idx += StringLen(search_key);

   // Determine if string or numeric
   int val_start = start_idx;
   bool is_string = false;
   while(StringSubstr(json, val_start, 1) == " " || StringSubstr(json, val_start, 1) == "\"") {
      if(StringSubstr(json, val_start, 1) == "\"") is_string = true;
      val_start++;
   }

   int val_end = val_start;
   while(val_end < StringLen(json)) {
      string c = StringSubstr(json, val_end, 1);
      if((is_string && c == "\"") || (!is_string && (c == "," || c == "}"))) {
         break;
      }
      val_end++;
   }

   return StringSubstr(json, val_start, val_end - val_start);
  }
