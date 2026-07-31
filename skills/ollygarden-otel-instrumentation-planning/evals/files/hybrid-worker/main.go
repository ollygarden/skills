package main

import (
	"context"
	"encoding/json"
	"net/http"
)

type Job struct {
	Kind    string `json:"kind"`
	Payload string `json:"payload"`
}

func submit(w http.ResponseWriter, r *http.Request) {
	var job Job
	_ = json.NewDecoder(r.Body).Decode(&job)
	queue.Publish(context.Background(), job)
	w.WriteHeader(http.StatusAccepted)
}

func consume(ctx context.Context, job Job) error {
	return processor.Run(ctx, job)
}

func main() {
	http.HandleFunc("/jobs", submit)
	http.HandleFunc("/ready", func(w http.ResponseWriter, _ *http.Request) { w.WriteHeader(200) })
	go queue.Consume(context.Background(), consume)
	http.ListenAndServe(":8080", nil)
}
