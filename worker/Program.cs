using System;
using System.Data.Common;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using Newtonsoft.Json;
using Npgsql;
using Confluent.Kafka;

namespace Worker
{
    public class Program
    {
        public static int Main(string[] args)
        {
            try
            {
                var pgsql = OpenDbConnection("Server=db;Username=postgres;Password=postgres;");
                var keepAliveCommand = pgsql.CreateCommand();
                keepAliveCommand.CommandText = "SELECT 1";

                var consumerConfig = new ConsumerConfig
                {
                    BootstrapServers = "kafka:29092",
                    GroupId = "vote-consumer-group",
                    AutoOffsetReset = AutoOffsetReset.Earliest
                };

                using (var consumer = new ConsumerBuilder<Ignore, string>(consumerConfig).Build())
                {
                    consumer.Subscribe("votes");

                    while (true)
                    {
                        try
                        {
                            var cr = consumer.Consume(CancellationToken.None);
                            var vote = JsonConvert.DeserializeObject<Vote>(cr.Value);

                            Console.WriteLine($"Processing vote for '{vote.vote}' by '{vote.voter_id}'");
                            if (!pgsql.State.Equals(System.Data.ConnectionState.Open))
                            {
                                Console.WriteLine("Reconnecting DB");
                                pgsql = OpenDbConnection("Server=db;Username=postgres;Password=postgres;");
                            }
                            UpdateVote(pgsql, vote.voter_id, vote.vote);
                        }
                        catch (ConsumeException e)
                        {
                            Console.WriteLine($"Error occurred: {e.Error.Reason}");
                        }
                        catch (Exception ex)
                        {
                            Console.Error.WriteLine(ex.ToString());
                        }

                        keepAliveCommand.ExecuteNonQuery();
                    }
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine(ex.ToString());
                return 1;
            }
        }

        private static NpgsqlConnection OpenDbConnection(string connectionString)
        {
            NpgsqlConnection connection;

            while (true)
            {
                try
                {
                    connection = new NpgsqlConnection(connectionString);
                    connection.Open();
                    break;
                }
                catch (SocketException)
                {
                    Console.Error.WriteLine("Waiting for db");
                    Thread.Sleep(1000);
                }
                catch (DbException)
                {
                    Console.Error.WriteLine("Waiting for db");
                    Thread.Sleep(1000);
                }
            }

            Console.Error.WriteLine("Connected to db");

            var command = connection.CreateCommand();
            command.CommandText = @"CREATE TABLE IF NOT EXISTS votes (
                                        id VARCHAR(255) NOT NULL UNIQUE,
                                        vote VARCHAR(255) NOT NULL
                                    )";
            command.ExecuteNonQuery();

            return connection;
        }

        private static void UpdateVote(NpgsqlConnection connection, string voterId, string vote)
        {
            var command = connection.CreateCommand();
            try
            {
                command.CommandText = "INSERT INTO votes (id, vote) VALUES (@id, @vote)";
                command.Parameters.AddWithValue("@id", voterId);
                command.Parameters.AddWithValue("@vote", vote);
                command.ExecuteNonQuery();
            }
            catch (DbException)
            {
                command.CommandText = "UPDATE votes SET vote = @vote WHERE id = @id";
                command.ExecuteNonQuery();
            }
            finally
            {
                command.Dispose();
            }
        }

        public class Vote
        {
            public string voter_id { get; set; }
            public string vote { get; set; }
        }
    }
}
