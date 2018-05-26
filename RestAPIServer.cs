using System;
using System.Collections.Specialized;
using System.Net;

namespace RestAPIServer
{
    class RestAPIServer
    {
        private HttpListener listener;

        public RestAPIServer(params string[] prefixes)
        {
            listener = new HttpListener();

            if (!HttpListener.IsSupported)
            {
                Console.WriteLine("Windows XP SP2 or Server 2003 is required to use the HttpListener class.");
                return;
            }

            foreach (string s in prefixes)
            {
                listener.Prefixes.Add(s);
            }
        }

        public void Stop()
        {
            listener.Stop();
            listener.Close();
        }

        public void Run()
        {
            listener.Start();
            Console.WriteLine("Hosting server.");
            while (listener.IsListening)
            {
                HttpListenerContext context = listener.GetContext();
                HttpListenerRequest request = context.Request;

                if (request.HttpMethod == "GET")
                {
                    // Check our URL
                    Uri query = request.Url;
                    NameValueCollection queryDictionary = System.Web.HttpUtility.ParseQueryString(query.Query);

                    // This is where you'd process arguments!

                    // Spit out a result
                    string body = "<HTML><BODY> ";
                    foreach (string key in queryDictionary)
                    {
                        body += String.Format("Key: {0}, Value: {1}<br>", key, queryDictionary[key]);
                    }
                    body += "</BODY></HTML>";
                    byte[] buffer = System.Text.Encoding.UTF8.GetBytes(body);

                    HttpListenerResponse response = context.Response;
                    response.ContentLength64 = buffer.Length;
                    System.IO.Stream output = response.OutputStream;
                    output.Write(buffer, 0, buffer.Length);
                    output.Close();
                } else
                {
                    continue;
                }
            }

            this.Stop();
        }
                
    }

    internal class RunMain
    {
        static void Main()
        {
            String url = "http://localhost:9000/";
            RestAPIServer server = new RestAPIServer(url);
            server.Run();
        }
    }
}
