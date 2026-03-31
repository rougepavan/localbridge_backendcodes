-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 31, 2026 at 02:50 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `app_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `exchange_requests`
--

CREATE TABLE `exchange_requests` (
  `id` int(11) NOT NULL,
  `sender_email` varchar(150) NOT NULL,
  `receiver_email` varchar(150) NOT NULL,
  `product_id` int(11) NOT NULL,
  `date` varchar(100) DEFAULT NULL,
  `time` varchar(100) DEFAULT NULL,
  `location` varchar(255) DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `lng` double DEFAULT NULL,
  `offer_text` text DEFAULT NULL,
  `offer_image` varchar(255) DEFAULT NULL,
  `status` varchar(50) DEFAULT 'Requested',
  `otp` varchar(6) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `exchange_requests`
--

INSERT INTO `exchange_requests` (`id`, `sender_email`, `receiver_email`, `product_id`, `date`, `time`, `location`, `lat`, `lng`, `offer_text`, `offer_image`, `status`, `otp`, `user_id`, `created_at`) VALUES
(8, 'avulasalmanraj@gmail.com', 'sandeepsandeepkumarreddy123@gmail.com', 3, '2026-03-31', '15:24', 'Neduncheri, Poonamallee, Thiruvallur, Tamil Nadu, 600124, India', 13.044837995099998, 80.0552698597312, 'hh', 'offer_1774889622.729489_offer_snap_1774889615928.jpg', 'Completed', '453173', NULL, '2026-03-30 16:53:42'),
(9, 'gangalapudifamily123@gmail.com', 'sandeepsandeepkumarreddy123@gmail.com', 5, 'Tue, Mar 31', 'Morning (9–12am)', '22F8+86J, Kuthambakkam, Tamil Nadu 602105, India', 13.023379834220252, 80.01579578965902, '1233', 'offer_1774938342.870927_offer_snap_1774938335619.jpg', 'Accepted', NULL, NULL, '2026-03-31 06:25:42'),
(10, 'pavanofficial897@gmail.com', 'divitisaiprasannakumar@gmail.com', 9, '2026-03-31', '21:57', 'Renigunta, Tirupati, Andhra Pradesh, 517520, India', 13.644574533143645, 79.49624735657812, 'hg', 'offer_1774945707.40319_Easiest-Ice-Cream-1-1-of-1.jpg', 'Completed', '406145', NULL, '2026-03-31 08:28:27');

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE `messages` (
  `id` int(11) NOT NULL,
  `exchange_id` int(11) NOT NULL,
  `sender_email` varchar(150) NOT NULL,
  `receiver_email` varchar(150) NOT NULL,
  `content` text NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp(),
  `image_name` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `messages`
--

INSERT INTO `messages` (`id`, `exchange_id`, `sender_email`, `receiver_email`, `content`, `timestamp`, `image_name`) VALUES
(12, 8, 'sandeepsandeepkumarreddy123@gmail.com', 'avulasalmanraj@gmail.com', 'hii', '2026-03-30 16:54:11', NULL),
(13, 10, 'pavanofficial897@gmail.com', 'divitisaiprasannakumar@gmail.com', 'hii', '2026-03-31 08:30:12', NULL),
(14, 10, 'divitisaiprasannakumar@gmail.com', 'pavanofficial897@gmail.com', 'hii', '2026-03-31 08:30:27', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `user_email` varchar(150) NOT NULL,
  `message` text NOT NULL,
  `type` varchar(50) DEFAULT 'info',
  `related_id` int(11) DEFAULT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`id`, `user_email`, `message`, `type`, `related_id`, `is_read`, `created_at`) VALUES
(1, 'pavanofficial897@gmail.com', 'yu requested your product!', 'info', 1, 1, '2026-03-22 10:36:06'),
(2, 'gangalapudifamily123@gmail.com', 'Your request was accepted!', 'accepted', 1, 1, '2026-03-22 10:36:35'),
(3, 'gangalapudifamily123@gmail.com', 'An exchange request was cancelled.', 'info', 1, 1, '2026-03-22 10:37:11'),
(4, 'komaldarisipudi@gmail.com', 'yu requested your product!', 'info', 2, 0, '2026-03-22 14:17:25'),
(5, 'komaldarisipudi@gmail.com', 'Yanamadala Siva pavan requested your product!', 'info', 3, 0, '2026-03-22 17:20:40'),
(6, 'royalreddy029@gmail.com', 'yu requested your product!', 'info', 4, 0, '2026-03-23 03:52:02'),
(7, 'komaldarisipudi@gmail.com', 'Sandeep requested your product!', 'info', 5, 0, '2026-03-23 07:32:06'),
(8, 'komaldarisipudi@gmail.com', 'Habeeb S. Habeeb requested your product!', 'info', 6, 0, '2026-03-24 03:54:11'),
(9, 'royalreddy029@gmail.com', 'Komal darisipudi requested your product!', 'info', 7, 0, '2026-03-24 05:14:24'),
(10, 'komaldarisipudi@gmail.com', 'Malli requested your product!', 'info', 8, 0, '2026-03-24 17:20:35'),
(11, 'komaldarisipudi@gmail.com', 'babu requested your product!', 'info', 9, 0, '2026-03-26 08:52:29'),
(12, 'gangalapudifamily123@gmail.com', 'pavan requested your product!', 'info', 1, 1, '2026-03-29 02:04:32'),
(13, 'gangalapudifamily123@gmail.com', 'Komal requested your product!', 'info', 2, 1, '2026-03-29 06:10:35'),
(14, 'gangalapudifamily123@gmail.com', 'lalith requested your product!', 'info', 3, 1, '2026-03-29 08:16:39'),
(15, 'gangalapudifamily123@gmail.com', 'raju requested your product!', 'info', 4, 1, '2026-03-29 10:33:33'),
(16, 'rajuavula986@gmail.com', 'Your request was accepted!', 'accepted', 4, 0, '2026-03-29 10:33:53'),
(17, 'gangalapudifamily123@gmail.com', 'Venku requested your product!', 'info', 5, 1, '2026-03-29 16:33:46'),
(18, 'venky275474@gmail.com', 'Trade successfully completed!', 'success', 5, 0, '2026-03-29 16:36:19'),
(19, 'gangalapudifamily123@gmail.com', 'Trade successfully completed!', 'success', 5, 1, '2026-03-29 16:36:19'),
(20, 'venky275474@gmail.com', 'Trade successfully completed!', 'success', 5, 0, '2026-03-29 16:36:56'),
(21, 'gangalapudifamily123@gmail.com', 'Trade successfully completed!', 'success', 5, 1, '2026-03-29 16:36:56'),
(22, 'venky275474@gmail.com', 'Trade successfully completed!', 'success', 5, 0, '2026-03-29 16:38:07'),
(23, 'gangalapudifamily123@gmail.com', 'Trade successfully completed!', 'success', 5, 1, '2026-03-29 16:38:07'),
(24, 'gangalapudifamily123@gmail.com', 'bob requested your product!', 'info', 6, 1, '2026-03-30 05:15:29'),
(25, 'homiezz2504@gmail.com', 'Your request was accepted!', 'accepted', 6, 0, '2026-03-30 05:16:11'),
(26, 'sandeepsandeepkumarreddy123@gmail.com', 'kumar requested your product!', 'info', 7, 1, '2026-03-30 05:21:07'),
(27, 'sandeepsandeepkumarreddy123@gmail.com', 'raju requested your product!', 'info', 8, 1, '2026-03-30 16:53:42'),
(28, 'avulasalmanraj@gmail.com', 'Your request was accepted!', 'accepted', 8, 0, '2026-03-30 16:53:58'),
(29, 'avulasalmanraj@gmail.com', 'sandeep updated meetup details for Fg', 'info', 8, 0, '2026-03-30 16:54:35'),
(30, 'avulasalmanraj@gmail.com', 'Trade successfully completed!', 'success', 8, 0, '2026-03-30 16:55:09'),
(31, 'sandeepsandeepkumarreddy123@gmail.com', 'Trade successfully completed!', 'success', 8, 1, '2026-03-30 16:55:09'),
(32, 'sandeepsandeepkumarreddy123@gmail.com', 'kumar requested your product!', 'info', 9, 0, '2026-03-31 06:25:42'),
(33, 'gangalapudifamily123@gmail.com', 'Your request was accepted!', 'accepted', 9, 0, '2026-03-31 06:28:19'),
(34, 'divitisaiprasannakumar@gmail.com', 'pavan requested your product!', 'info', 10, 0, '2026-03-31 08:28:27'),
(35, 'pavanofficial897@gmail.com', 'Your request was accepted!', 'accepted', 10, 0, '2026-03-31 08:28:46'),
(36, 'divitisaiprasannakumar@gmail.com', 'pavan updated meetup details for seoul', 'info', 10, 0, '2026-03-31 08:29:39'),
(37, 'pavanofficial897@gmail.com', 'Trade successfully completed!', 'success', 10, 0, '2026-03-31 08:32:09'),
(38, 'divitisaiprasannakumar@gmail.com', 'Trade successfully completed!', 'success', 10, 0, '2026-03-31 08:32:09');

-- --------------------------------------------------------

--
-- Table structure for table `products`
--

CREATE TABLE `products` (
  `id` int(11) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text DEFAULT NULL,
  `image_name` varchar(255) DEFAULT NULL,
  `user_name` varchar(150) DEFAULT NULL,
  `category` varchar(100) DEFAULT NULL,
  `expiry_date` date DEFAULT NULL,
  `freshness` varchar(50) DEFAULT NULL,
  `used_for` varchar(100) DEFAULT NULL,
  `item_condition` varchar(50) DEFAULT NULL,
  `return_offer` text DEFAULT NULL,
  `distance` float DEFAULT 0,
  `rating` float DEFAULT 5,
  `lat` double DEFAULT NULL,
  `lng` double DEFAULT NULL,
  `quantity` varchar(50) DEFAULT NULL,
  `unit` varchar(20) DEFAULT NULL,
  `ai_insight` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` varchar(50) DEFAULT 'Active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `products`
--

INSERT INTO `products` (`id`, `name`, `description`, `image_name`, `user_name`, `category`, `expiry_date`, `freshness`, `used_for`, `item_condition`, `return_offer`, `distance`, `rating`, `lat`, `lng`, `quantity`, `unit`, `ai_insight`, `created_at`, `status`) VALUES
(3, 'Fg', 'hj', '1774862525.822349_post_1774862528382.jpg', 'sandeepsandeepkumarreddy123@gmail.com', 'Others', '0000-00-00', 'Today Cooked', 'hg', 'Good', 'yy', 0, 5, 13.0264895, 80.0160066, 'hg', '', NULL, '2026-03-30 09:22:05', 'Completed'),
(4, 'mountain dew', 'drink', '1774921287.809067_images.jpg', 'pavanofficial897@gmail.com', 'Liquids', '2026-04-22', '1-2 Days Old', '', '', 'Sprite or anything', 0, 0, 13.047695827111243, 80.05230712886483, '3', 'l', NULL, '2026-03-31 01:41:27', 'Active'),
(5, 'ice cream', 'vanila iccream', '1774921414.618607_Easiest-Ice-Cream-1-1-of-1.jpg', 'sandeepsandeepkumarreddy123@gmail.com', 'Food', '2026-04-28', '1-2 Days Old', '', '', 'choclates', 0, 5, 13.047684821084536, 80.05231766426353, '300', 'g', NULL, '2026-03-31 01:43:34', 'Active'),
(6, 'Xbvx', 'vxvx', '1774926979.931786_post_1774926980893.jpg', 'gangalapudifamily123@gmail.com', 'Others', '0000-00-00', 'Today Cooked', 'vzvx', 'Good', '', 0, 5, 13.086071800639056, 80.00750843435526, 'vzvx', '', NULL, '2026-03-31 03:16:19', 'Active'),
(7, 'cc', 'cdd', '1774933173.04114_Gemini_Generated_Image_netrk5netrk5netr.png', 'pavanofficial897@gmail.com', 'Others', '0000-00-00', '', '2', 'Like New', 'm', 0, 0, 13.65046464323779, 79.50205264967127, '', NULL, NULL, '2026-03-31 04:59:33', 'Active'),
(8, 'meAals', 'fg', '1774944925.338685_525304231_1456430842345204_3156763859586518871_n.jpg', 'divitisaiprasannakumar@gmail.com', 'Food', '0000-00-00', NULL, '', '', '', 0, 5, 13.027087384850335, 80.0172831985339, '500', 'g', NULL, '2026-03-31 08:15:25', 'Active'),
(9, 'seoul', 'dfsd', '1774945596.792474_Contest-Winning-Broccoli-Chicken-Casserole_exps37392_TH143193B04_22_3bC_RMS-12.jpg', 'divitisaiprasannakumar@gmail.com', 'Food', '2026-04-22', '1-2 Days Old', '', '', 'dd', 0, 5, 13.6465436, 79.4999617, '34', 'g', NULL, '2026-03-31 08:26:36', 'Completed');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(150) NOT NULL,
  `password` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `location` varchar(200) DEFAULT NULL,
  `bio` text DEFAULT NULL,
  `preferred_exchange` varchar(50) DEFAULT 'Meetup',
  `profile_image` varchar(255) DEFAULT NULL,
  `trades` int(11) DEFAULT 0,
  `rating` float DEFAULT 5,
  `trust` int(11) DEFAULT 100,
  `reset_otp` varchar(10) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `password`, `phone`, `location`, `bio`, `preferred_exchange`, `profile_image`, `trades`, `rating`, `trust`, `reset_otp`, `created_at`) VALUES
(1, 'pavan', 'pavanofficial897@gmail.com', 'scrypt:32768:8:1$jG5oJ9CR7KjIpGwl$e9c86b12b80a29820785ea0da500be5c55072f8c01ea529d65d7fd77803b637f495f92396dc35d3bb5e0cc9e243b345864db5fa8efdd510a84374da07c701b1e', '', '22H8+654, Kuthambakkam, Sriperumbudur, Tamil Nadu, India - 602105', '', 'Delivery', 'profile_1774932239.574603_', 1, 5, 68, NULL, '2026-03-28 18:11:01'),
(2, 'kumar', 'gangalapudifamily123@gmail.com', 'scrypt:32768:8:1$2dk5LsIrlgTbTDye$19992473c0eb1e180e7fda892486f42feebf270a4d179e03449b6b365d0ae870ef5ab6ac1d3de52a737f5cc5f10f81db1a7b1504c075720b2b2632ccf3a71fbc', '', 'chennai', '', 'Meetup', 'profile_1774772488.238885_profile_temp.jpg', 3, 5, 80, NULL, '2026-03-29 01:40:45'),
(3, 'Komal', 'komaldarisipudi@gmail.com', 'scrypt:32768:8:1$iLkZHyem59lbCmMc$24ac8c992e4c86d84920db943158f67972904757b9e09f58275642e1e990403983139912b8689196e603d4a9214b5f311abf967633ff640189717d85525fa3c6', NULL, 'Block H, Tiruvallur, Nemam, Tamil Nadu, India - 600124', NULL, 'Meetup', NULL, 0, 0, 50, NULL, '2026-03-29 06:09:52'),
(4, 'lalith', 'lalithcg08@gmail.com', 'scrypt:32768:8:1$WPEwIyBEbdRt8Ftr$0a42fee7a9672269102ab61bce120418817628cb05216d813133d29af6f78e5df41299b8d39ca0ae74fb1aa4a0229b64889141c9865b2cc7da84ce2da6aafc8d', NULL, 'Block H, Tiruvallur, Nemam, Tamil Nadu, India - 600124', NULL, 'Meetup', NULL, 0, 0, 50, NULL, '2026-03-29 08:15:03'),
(5, 'raju', 'rajuavula986@gmail.com', 'scrypt:32768:8:1$ISDTwaFNHQ2DwiAL$237f419a00f1a124ee7c0982cbbfd1422cd80131476773ace8964bf9fb4422e82a324dda8c819cdf16082a6fe960762c60d5eccd0d7f73e7bfe2161d8bcaefee', NULL, 'Block H, 001, Tiruvallur, Nemam, Tamil Nadu, India - 600124', NULL, 'Meetup', NULL, 0, 0, 50, NULL, '2026-03-29 10:31:03'),
(6, 'Venku', 'venky275474@gmail.com', 'scrypt:32768:8:1$gmeA8HFPT049h5kv$8d0e02ea841b0d0372bc31a53b4196d251898c354cb1b4194453e8a1869152ce206e3edca7bddf7dc3d3d9dc92df05b0a4dcd2dde81927c5b3c3d7e4db43b2f8', NULL, 'Block G, Thirumazhisai, Nemam, Tamil Nadu, India - 600124', NULL, 'Meetup', NULL, 3, 5, 80, NULL, '2026-03-29 16:32:48'),
(7, 'sandeep', 'sandeepsandeepkumarreddy123@gmail.com', 'scrypt:32768:8:1$N3qavluVlDp6RY6C$f0feffbe962672a60120ac88273986bd44d77e2ca0336c24fdfc0b10d363f5e249c390bbcb8702c3e272a620cef006b1d9d23c6635ebdff7216c20ff8ed1f301', NULL, 'EEE Department, Kuthambakkam, Sriperumbudur, Tamil Nadu, India - 602105', NULL, 'Meetup', NULL, 1, 5, 68, NULL, '2026-03-30 03:11:01'),
(8, 'bob', 'homiezz2504@gmail.com', 'scrypt:32768:8:1$H51X3ctZPD3amAav$35419fcb251071890f1348338de194a1f32b2b3b5248d23bcfd2ecbe3e2139dcc122725f91935c6a1c74b9b1d40a58ee11511fdd861cfdca2cf2dab48cdd3ef7', '', '22G8+Q5X, Kuthambakkam, Sriperumbudur, Tamil Nadu, India - 602105', '', 'Meetup', NULL, 0, 0, 50, NULL, '2026-03-30 05:13:33'),
(9, '34567', 'puttapradeep2005@gmail.com', 'scrypt:32768:8:1$Rh6aD0gTNpK20uBj$bf6cf91fdc7593a06387807bccfdda72b46d1b2e2347bba58f744d8418391e53bd378061367493155e052dbbbc4f489aa44281f5dcada9f5c57b2bd6b91d7766', NULL, '22G8+C47, Kuthambakkam, Sriperumbudur, Tamil Nadu, India - 602105', NULL, 'Meetup', NULL, 0, 0, 50, NULL, '2026-03-30 08:22:00'),
(10, 'Habeeb', 's.mohammadhabeeb786@gmail.com', 'scrypt:32768:8:1$3hbbdbnaPzHY1x89$7fe3b0cd0136475a73389d5f5ea72d55769cbeb37f3636486e21a898d8696d3717fb93a25fbb727794192521fe04145fba2ea405d1d87cb74096ecfafec6da7b', NULL, 'EEE Department, Kuthambakkam, Sriperumbudur, Tamil Nadu, India - 602105', NULL, 'Meetup', NULL, 0, 0, 50, NULL, '2026-03-30 09:07:31'),
(11, 'Pavankum', 'pavanbackup778@gmail.com', 'scrypt:32768:8:1$OMB8Fgq8klt7c9h4$673242515d3ee54632b093809ad9366b848f09c7c631cfd9aa3892bdf24164dffc5a766c7da6d972961652653e85eff44ea12033f2425e6d7c696916ec5dd049', NULL, 'EEE Department, Kuthambakkam, Sriperumbudur, Tamil Nadu, India - 602105', NULL, 'Meetup', NULL, 0, 0, 50, NULL, '2026-03-30 09:28:47'),
(12, 'raju', 'avulasalmanraj@gmail.com', 'scrypt:32768:8:1$Fpf78087b9bUTkU8$c369deedaadb2e54445e26b21ae55a664d7af653a72c0b7fc7cf9aec9a608e52951b775d16b48e5d825234d0a78b46ec4443776c3b2d3df567f7bfe89bfe8976', NULL, 'Block H, Tiruvallur, Nemam, Tamil Nadu, India - 600124', NULL, 'Meetup', NULL, 1, 5, 68, NULL, '2026-03-30 16:51:34'),
(13, 'sai', 'divitisaiprasannakumar@gmail.com', 'scrypt:32768:8:1$usVkySh0huPL9wKD$ca6aa59cf1d0ff36e7c5a04f24c9c0a336327635e9cf9ca68dd14433ac9282d872a74ec579e96aa05f30a36daef5ee02cb83a0b9767860b690c048266bdf8d98', NULL, 'Anantapur', NULL, 'Meetup', NULL, 1, 5, 68, NULL, '2026-03-31 08:11:26');

-- --------------------------------------------------------

--
-- Table structure for table `user_locations`
--

CREATE TABLE `user_locations` (
  `id` int(11) NOT NULL,
  `user_email` varchar(150) NOT NULL,
  `label` varchar(50) DEFAULT NULL,
  `address` text DEFAULT NULL,
  `lat` double DEFAULT NULL,
  `lng` double DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `user_locations`
--

INSERT INTO `user_locations` (`id`, `user_email`, `label`, `address`, `lat`, `lng`, `created_at`) VALUES
(2, 'gangalapudifamily123@gmail.com', 'Home', 'JGH2+P9Q, Tirupati, Andhra Pradesh - 517520', 13.629220263041935, 79.50104534626007, '2026-03-31 05:25:55'),
(4, 'pavanofficial897@gmail.com', 'Home', 'JC8M+HJ5, Korramenugunta, Tirupati, Andhra Pradesh - 517503', 13.616035305022002, 79.4338097423315, '2026-03-31 06:41:53');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `exchange_requests`
--
ALTER TABLE `exchange_requests`
  ADD PRIMARY KEY (`id`),
  ADD KEY `product_id` (`product_id`);

--
-- Indexes for table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `exchange_id` (`exchange_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `products`
--
ALTER TABLE `products`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_name` (`user_name`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `user_locations`
--
ALTER TABLE `user_locations`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_email` (`user_email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `exchange_requests`
--
ALTER TABLE `exchange_requests`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=39;

--
-- AUTO_INCREMENT for table `products`
--
ALTER TABLE `products`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;

--
-- AUTO_INCREMENT for table `user_locations`
--
ALTER TABLE `user_locations`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `exchange_requests`
--
ALTER TABLE `exchange_requests`
  ADD CONSTRAINT `exchange_requests_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `messages`
--
ALTER TABLE `messages`
  ADD CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`exchange_id`) REFERENCES `exchange_requests` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `products`
--
ALTER TABLE `products`
  ADD CONSTRAINT `products_ibfk_1` FOREIGN KEY (`user_name`) REFERENCES `users` (`email`) ON DELETE CASCADE;

--
-- Constraints for table `user_locations`
--
ALTER TABLE `user_locations`
  ADD CONSTRAINT `user_locations_ibfk_1` FOREIGN KEY (`user_email`) REFERENCES `users` (`email`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
