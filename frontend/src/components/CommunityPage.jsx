import { useState, useEffect, useRef } from "react";
import { useToast } from "@chakra-ui/react";
import { MessageSquare, Send, ChevronDown, ChevronUp, Trash2, Trophy } from "lucide-react";
import Navbar from "./Navbar";
import {
  getCommunityPosts, createCommunityPost,
  getCommunityReplies, createCommunityReply,
  deleteCommunityPost, deleteCommunityReply,
  getCommunityLeaderboard,
} from "../api";
import "../styles/community.css";

const RANK_THRESHOLDS = [
  { min: 500, rank: "Legend",        emoji: "🚀", color: "#7C3AED" },
  { min: 200, rank: "Diamond",       emoji: "💎", color: "#06B6D4" },
  { min: 100, rank: "Gold Member",   emoji: "🥇", color: "#D97706" },
  { min:  50, rank: "Silver Member", emoji: "🥈", color: "#64748B" },
  { min:  10, rank: "Member",        emoji: "🔵", color: "#2563EB" },
  { min:   0, rank: "Newbie",        emoji: "🤖", color: "#94A3B8" },
];

const getRank = (total) =>
  RANK_THRESHOLDS.find((t) => total >= t.min) || RANK_THRESHOLDS.at(-1);

const RankBadge = ({ rankInfo }) => {
  const r = rankInfo || getRank(0);
  return (
    <span className="cm-rank-badge" style={{ borderColor: r.color, color: r.color }}>
      {r.emoji} {r.rank}
    </span>
  );
};

const formatTime = (iso) => {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
};

const PostCard = ({ post, user, authToken, isAdmin, onDeleted }) => {
  const [replies, setReplies] = useState([]);
  const [showReplies, setShowReplies] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [repliesLoading, setRepliesLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const toast = useToast();

  const loadReplies = async () => {
    setRepliesLoading(true);
    try {
      const data = await getCommunityReplies(authToken, post.id);
      setReplies(Array.isArray(data) ? data : []);
    } catch {
      setReplies([]);
    } finally {
      setRepliesLoading(false);
    }
  };

  const toggleReplies = async () => {
    if (!showReplies && replies.length === 0) await loadReplies();
    setShowReplies((v) => !v);
  };

  const handleReply = async () => {
    if (!replyText.trim()) return;
    setSending(true);
    try {
      const reply = await createCommunityReply(authToken, post.id, replyText.trim());
      setReplies((prev) => [...prev, reply]);
      setReplyText("");
      if (!showReplies) setShowReplies(true);
    } catch (e) {
      toast({
        title: e?.response?.data?.detail || "Failed to reply",
        status: "error", duration: 3000, isClosable: true,
      });
    } finally {
      setSending(false);
    }
  };

  const handleDeletePost = async () => {
    if (!window.confirm("Delete this post and all its replies?")) return;
    try {
      await deleteCommunityPost(authToken, post.id);
      onDeleted(post.id);
    } catch (e) {
      toast({ title: e?.response?.data?.detail || "Delete failed", status: "error", duration: 3000, isClosable: true });
    }
  };

  const handleDeleteReply = async (replyId) => {
    try {
      await deleteCommunityReply(authToken, replyId);
      setReplies((prev) => prev.filter((r) => r.id !== replyId));
    } catch (e) {
      toast({ title: e?.response?.data?.detail || "Delete failed", status: "error", duration: 3000, isClosable: true });
    }
  };

  const canDeletePost = isAdmin || post.user_id === user?.id;

  return (
    <div className="cm-post-card">
      <div className="cm-post-header">
        <div className="cm-post-author">
          <div className="cm-avatar">{post.user_name?.[0]?.toUpperCase() || "?"}</div>
          <div>
            <div className="cm-post-name">{post.user_name}</div>
            <RankBadge rankInfo={post.rank_info} />
          </div>
        </div>
        <div className="cm-post-meta">
          <span className="cm-post-time">{formatTime(post.created_at)}</span>
          {canDeletePost && (
            <button className="cm-delete-btn" onClick={handleDeletePost} title="Delete post">
              <Trash2 size={14} />
            </button>
          )}
        </div>
      </div>

      <p className="cm-post-content">{post.content}</p>

      <div className="cm-post-actions">
        <button className="cm-reply-toggle" onClick={toggleReplies}>
          <MessageSquare size={14} />
          {post.reply_count + (replies.length > post.reply_count ? replies.length - post.reply_count : 0)} {" "}
          {showReplies ? "Hide" : "Show"} Replies
          {showReplies ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        </button>
      </div>

      {showReplies && (
        <div className="cm-replies">
          {repliesLoading ? (
            <p className="cm-loading">Loading replies...</p>
          ) : replies.length === 0 ? (
            <p className="cm-no-replies">No replies yet. Be the first!</p>
          ) : (
            replies.map((r) => (
              <div key={r.id} className="cm-reply-card">
                <div className="cm-reply-header">
                  <div className="cm-reply-author">
                    <div className="cm-avatar cm-avatar--sm">{r.user_name?.[0]?.toUpperCase() || "?"}</div>
                    <div>
                      <span className="cm-reply-name">{r.user_name}</span>
                      <RankBadge rankInfo={r.rank_info} />
                    </div>
                  </div>
                  <div className="cm-post-meta">
                    <span className="cm-post-time">{formatTime(r.created_at)}</span>
                    {(isAdmin || r.user_id === user?.id) && (
                      <button className="cm-delete-btn" onClick={() => handleDeleteReply(r.id)}>
                        <Trash2 size={12} />
                      </button>
                    )}
                  </div>
                </div>
                <p className="cm-reply-content">{r.content}</p>
              </div>
            ))
          )}

          {/* Reply input */}
          <div className="cm-reply-form">
            <textarea
              className="cm-reply-input"
              placeholder="Write a reply..."
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              rows={2}
              maxLength={500}
            />
            <div className="cm-reply-form-footer">
              <span className="cm-char-count">{replyText.length}/500</span>
              <button
                className="cm-send-btn"
                onClick={handleReply}
                disabled={sending || !replyText.trim()}
              >
                <Send size={14} /> {sending ? "Sending..." : "Reply"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const CommunityPage = ({ user, authToken, onLogout, onNavigate, onAdminAccess }) => {
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [newPost, setNewPost] = useState("");
  const [posting, setPosting] = useState(false);
  const [leaderboard, setLeaderboard] = useState([]);
  const toast = useToast();
  const isAdmin = user?.role === "admin";

  const loadPosts = async (p = 1, append = false) => {
    setLoading(true);
    try {
      const data = await getCommunityPosts(authToken, p, 20);
      setTotal(data.total || 0);
      setPosts((prev) => append ? [...prev, ...(data.posts || [])] : (data.posts || []));
    } catch {
      toast({ title: "Failed to load posts", status: "error", duration: 3000, isClosable: true });
    } finally {
      setLoading(false);
    }
  };

  const loadLeaderboard = async () => {
    try {
      const data = await getCommunityLeaderboard(authToken);
      setLeaderboard(Array.isArray(data) ? data : []);
    } catch { }
  };

  useEffect(() => {
    loadPosts(1);
    loadLeaderboard();
  }, [authToken]);

  const handlePost = async () => {
    if (!newPost.trim()) return;
    setPosting(true);
    try {
      const post = await createCommunityPost(authToken, newPost.trim());
      setPosts((prev) => [post, ...prev]);
      setTotal((t) => t + 1);
      setNewPost("");
      loadLeaderboard();
    } catch (e) {
      toast({
        title: e?.response?.data?.detail || "Failed to post",
        status: "error", duration: 3000, isClosable: true,
      });
    } finally {
      setPosting(false);
    }
  };

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    loadPosts(nextPage, true);
  };

  const handlePostDeleted = (postId) => {
    setPosts((prev) => prev.filter((p) => p.id !== postId));
    setTotal((t) => t - 1);
  };

  const hasMore = posts.length < total;

  return (
    <div className="cm-page">
      <Navbar
        user={user}
        onNavigate={onNavigate}
        currentPage="community"
        onLogout={onLogout}
        onAdminAccess={onAdminAccess}
      />

      <div className="cm-container">
        <div className="cm-main">
          {/* Header */}
          <div className="cm-header">
            <h1 className="cm-title">Community</h1>
            <p className="cm-subtitle">Share ideas, ask questions, and connect with other robotics students.</p>
          </div>

          {/* New post form */}
          <div className="cm-compose">
            <div className="cm-compose-avatar">{user?.name?.[0]?.toUpperCase() || "?"}</div>
            <div className="cm-compose-right">
              <textarea
                className="cm-compose-input"
                placeholder="Share something with the community..."
                value={newPost}
                onChange={(e) => setNewPost(e.target.value)}
                rows={3}
                maxLength={1000}
              />
              <div className="cm-compose-footer">
                <span className="cm-char-count">{newPost.length}/1000</span>
                <button
                  className="cm-post-btn"
                  onClick={handlePost}
                  disabled={posting || !newPost.trim()}
                >
                  <Send size={15} /> {posting ? "Posting..." : "Post"}
                </button>
              </div>
            </div>
          </div>

          {/* Post list */}
          {loading && posts.length === 0 ? (
            <div className="cm-loading-center">Loading community posts...</div>
          ) : posts.length === 0 ? (
            <div className="cm-empty">
              <p>No posts yet. Be the first to share something!</p>
            </div>
          ) : (
            <>
              {posts.map((post) => (
                <PostCard
                  key={post.id}
                  post={post}
                  user={user}
                  authToken={authToken}
                  isAdmin={isAdmin}
                  onDeleted={handlePostDeleted}
                />
              ))}
              {hasMore && (
                <button className="cm-load-more" onClick={handleLoadMore} disabled={loading}>
                  {loading ? "Loading..." : "Load more posts"}
                </button>
              )}
            </>
          )}
        </div>

        {/* Sidebar */}
        <div className="cm-sidebar">
          {/* Your rank */}
          <div className="cm-sidebar-card">
            <h3 className="cm-sidebar-title">Your Rank</h3>
            <div className="cm-your-rank">
              <div className="cm-your-rank-name">{user?.name}</div>
              <RankBadge rankInfo={getRank(
                leaderboard.find((u2) => u2.user_id === user?.id)?.total_messages || 0
              )} />
              <div className="cm-your-rank-count">
                {leaderboard.find((u2) => u2.user_id === user?.id)?.total_messages || 0} messages
              </div>
            </div>
            <div className="cm-rank-guide">
              {RANK_THRESHOLDS.slice().reverse().map((t) => (
                <div key={t.rank} className="cm-rank-row" style={{ color: t.color }}>
                  <span>{t.emoji} {t.rank}</span>
                  <span className="cm-rank-req">{t.min}+ msgs</span>
                </div>
              ))}
            </div>
          </div>

          {/* Leaderboard */}
          <div className="cm-sidebar-card">
            <h3 className="cm-sidebar-title"><Trophy size={15} /> Top Members</h3>
            <div className="cm-leaderboard">
              {leaderboard.map((entry, i) => (
                <div key={entry.user_id} className="cm-leaderboard-row">
                  <span className="cm-leaderboard-rank">
                    {i === 0 ? "🥇" : i === 1 ? "🥈" : i === 2 ? "🥉" : `${i + 1}.`}
                  </span>
                  <span className="cm-leaderboard-name">{entry.user_name}</span>
                  <span className="cm-leaderboard-count">{entry.total_messages}</span>
                </div>
              ))}
              {leaderboard.length === 0 && (
                <p style={{ color: "#94a3b8", fontSize: 13 }}>No activity yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CommunityPage;
